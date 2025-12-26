# -*- coding: utf-8 -*-

with open('handlers/admin_handlers.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 559-584 qatorlarni almashtirish
new_lines = []
skip_until = -1

for i, line in enumerate(lines):
    if i + 1 >= 559 and i + 1 <= 583:
        if i + 1 == 559:
            # Yangi kod qo'shish
            new_lines.append('    # Baza kanalga yuboriladigan caption - chiroyli shrift\n')
            new_lines.append('    caption = (\n')
            new_lines.append("        f\"🎬 𝗡𝗼𝗺𝗶: {data['title']}\\n\\n\"\n")
            new_lines.append("        f\"🎭 𝗝𝗮𝗻𝗿: {data['genre']}\\n\"\n")
            new_lines.append("        f\"⏱ 𝗗𝗮𝘃𝗼𝗺𝗶𝘆𝗹𝗶𝗴𝗶: {data['duration']}\\n\"\n")
            new_lines.append("        f\"🔢 𝗞𝗼𝗱: {code}\\n\\n\"\n")
            new_lines.append("        f\"▶️ 𝗞𝗶𝗻𝗼𝗻𝗶 𝗸𝗼'𝗿𝗶𝘀𝗵: {bot_link}\"\n")
            new_lines.append('    )\n')
            new_lines.append('    \n')
            new_lines.append('    # Kinoni baza kanalga yuborish (tugmasiz)\n')
            new_lines.append('    try:\n')
            new_lines.append('        sent_message = await message.bot.send_video(\n')
            new_lines.append('            chat_id=base_channel_id,\n')
            new_lines.append("            video=data['file_id'],\n")
            new_lines.append('            caption=caption\n')
            new_lines.append('        )\n')
        continue
    else:
        new_lines.append(line)

with open('handlers/admin_handlers.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Caption updated successfully!')
