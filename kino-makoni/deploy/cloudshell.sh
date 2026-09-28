#!/usr/bin/env bash
# Kino Makoni — AWS CloudShell'dan bot serveriga o'rnatish (.pem kalit kerak emas).
#
# AWS Console → CloudShell (istalgan region — server IP bo'yicha barcha regionlardan topiladi):
#   curl -fsSL https://raw.githubusercontent.com/ibrohimkomilov001-web/kinobot/refs/heads/claude/eager-lovelace-0db0j8/kino-makoni/deploy/cloudshell.sh -o cs.sh
#   TG_API_ID=... TG_API_HASH=... TG_HELPER_BOT_TOKEN=... bash cs.sh
#
# Nima qiladi:
#   1. AWS akkaunt ID'si va bot serveri (SERVER_IP) instance'ini topadi
#   2. Security group'da 80/443 ni ochadi (Caddy HTTPS uchun)
#   3. CloudShell IP'siga VAQTINCHA 22-port ochadi, EC2 Instance Connect bilan
#      60 soniyalik kalit yuboradi va serverda bootstrap.sh ni ishga tushiradi
#   4. Oxirida vaqtinchalik 22-port qoidasini o'chiradi
set -euo pipefail

SERVER_IP="${SERVER_IP:-3.127.203.19}"
DOMAIN="${DOMAIN:-kinomakoni.uz}"
RAW="https://raw.githubusercontent.com/ibrohimkomilov001-web/kinobot/refs/heads/claude/eager-lovelace-0db0j8/kino-makoni/deploy/bootstrap.sh"

say()  { printf '\n\033[1;33m==> %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m  ✓ %s\033[0m\n' "$*"; }
warn() { printf '\033[1;31m  ! %s\033[0m\n' "$*"; }
die()  { printf '\n\033[1;31mXATO: %s\033[0m\n' "$*" >&2; exit 1; }

: "${TG_API_ID:?TG_API_ID berilmagan}"
: "${TG_API_HASH:?TG_API_HASH berilmagan}"
: "${TG_HELPER_BOT_TOKEN:?TG_HELPER_BOT_TOKEN berilmagan}"

say "AWS akkaunt"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)" || die "AWS CLI ishlamadi"
ok "Akkaunt ID: $ACCOUNT"

say "Bot serveri qidirilmoqda ($SERVER_IP)"
lookup() { # lookup REGION -> "IID SG STATE" yoki bo'sh
  aws ec2 describe-instances --region "$1" \
    --filters "Name=ip-address,Values=$SERVER_IP" \
    --query 'Reservations[0].Instances[0].[InstanceId, SecurityGroups[0].GroupId, State.Name]' \
    --output text 2>/dev/null | grep -v '^None' || true
}
REGION="" INFO=""
# Avval ehtimoliy regionlar (3.12x.x.x — Frankfurt), keyin barcha yoqilgan regionlar
for r in ${KM_REGION:-} eu-central-1 ${AWS_REGION:-} \
         $(aws ec2 describe-regions --query 'Regions[].RegionName' --output text 2>/dev/null); do
  INFO="$(lookup "$r")"
  if [ -n "$INFO" ]; then REGION="$r"; break; fi
done
[ -n "$REGION" ] || die "$SERVER_IP IP'li instance hech bir regionda topilmadi"
# Keyingi barcha aws buyruqlari shu regionda (CloudShell'ning AWS_REGION'idan ustun)
export AWS_REGION="$REGION" AWS_DEFAULT_REGION="$REGION"
read -r IID SG STATE <<< "$INFO"
ok "Instance: $IID ($STATE), region: $REGION, security group: $SG"

# open_port PORT CIDR TAVSIF  → "added" | "exists"
open_port() {
  local out
  if out="$(aws ec2 authorize-security-group-ingress --group-id "$SG" \
      --ip-permissions "IpProtocol=tcp,FromPort=$1,ToPort=$1,IpRanges=[{CidrIp=$2,Description=$3}]" 2>&1)"; then
    echo added
  elif [[ "$out" == *InvalidPermission.Duplicate* ]]; then
    echo exists
  else
    die "$1-portni ochib bo'lmadi: $out"
  fi
}

say "80/443 portlar (HTTPS)"
for p in 80 443; do
  r="$(open_port "$p" 0.0.0.0/0 kino-makoni-web)"
  ok "port $p: $([ "$r" = added ] && echo ochildi || echo "allaqachon ochiq")"
done

say "Vaqtinchalik SSH (faqat shu CloudShell IP'si uchun)"
MYIP="$(curl -fsS -m 10 https://checkip.amazonaws.com | tr -d '[:space:]')"
[ -n "$MYIP" ] || die "CloudShell IP'sini aniqlab bo'lmadi"
SSH_RULE="$(open_port 22 "$MYIP/32" kino-makoni-cloudshell-temp)"
cleanup() {
  if [ "${SSH_RULE:-}" = added ]; then
    if aws ec2 revoke-security-group-ingress --group-id "$SG" \
        --ip-permissions "IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=$MYIP/32}]" >/dev/null 2>&1; then
      ok "vaqtinchalik 22-port qoidasi o'chirildi"
    else
      warn "22-port qoidasini qo'lda o'chiring: $MYIP/32 ($SG)"
    fi
  fi
  rm -f "${KEY:-/nonexistent}" "${KEY:-/nonexistent}.pub"
}
trap cleanup EXIT
ok "22-port: $MYIP/32 ($SSH_RULE)"

KEY="$(mktemp -u "$HOME/.km_key_XXXXXX")"
ssh-keygen -t ed25519 -f "$KEY" -N '' -q
aws ec2-instance-connect send-ssh-public-key --instance-id "$IID" \
  --instance-os-user ubuntu --ssh-public-key "file://$KEY.pub" >/dev/null \
  || die "EC2 Instance Connect kalit yubora olmadi"
ok "60 soniyalik kalit yuborildi"

say "Serverda bootstrap.sh ishga tushirilmoqda (3-8 daqiqa)"
REMOTE="curl -fsSL $(printf %q "$RAW") -o ~/bootstrap.sh && \
TG_API_ID=$(printf %q "$TG_API_ID") TG_API_HASH=$(printf %q "$TG_API_HASH") \
TG_HELPER_BOT_TOKEN=$(printf %q "$TG_HELPER_BOT_TOKEN") DOMAIN=$(printf %q "$DOMAIN") \
bash ~/bootstrap.sh"
ssh -i "$KEY" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 \
  -o ServerAliveInterval=30 "ubuntu@$SERVER_IP" "$REMOTE" \
  || die "Serverdagi o'rnatish xato bilan tugadi (yuqoridagi natijaga qarang)"

say "Tayyor"
echo "  Tekshirish: curl https://api.$DOMAIN/health"
