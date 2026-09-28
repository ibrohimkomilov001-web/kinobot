import SwiftUI

/// "Premium kerak" oynasi (playback premium_required qaytarganda)
struct PremiumSheet: View {
    let prompt: PremiumPrompt

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 18) {
            Image(systemName: "crown.fill")
                .font(.system(size: 34, weight: .bold))
                .foregroundStyle(Theme.accentGradient)
                .frame(width: 80, height: 80)
                .glassEffect(.regular.tint(Theme.accent.opacity(0.22)), in: .circle)
                .padding(.top, 8)

            Text("Bu kino Premium obunachilar uchun")
                .font(.title3.weight(.bold))
                .foregroundStyle(Theme.textPrimary)
                .multilineTextAlignment(.center)

            Text(messageText)
                .font(.subheadline)
                .foregroundStyle(Theme.textSecondary)
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)

            Button {
                dismiss()
            } label: {
                Text("Tushunarli")
                    .fontWeight(.bold)
                    .foregroundStyle(Theme.onAccent)
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.glassProminent)
            .tint(Theme.accent)
            .controlSize(.large)
            .padding(.top, 4)
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 20)
        .presentationDetents([.medium])
        .presentationDragIndicator(.visible)
    }

    private var messageText: String {
        "«\(prompt.titleName)» faqat Premium obunachilarga ochiq. Premium obuna tez orada ilovada paydo bo'ladi — hozircha boshqa kinolarni bepul tomosha qilishingiz mumkin."
    }
}

#Preview {
    Color.black
        .sheet(isPresented: .constant(true)) {
            PremiumSheet(prompt: PremiumPrompt(titleName: "Yulduzlar yo'li"))
        }
        .preferredColorScheme(.dark)
}
