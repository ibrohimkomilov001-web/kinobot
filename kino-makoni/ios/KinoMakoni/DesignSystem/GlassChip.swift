import SwiftUI

/// Liquid Glass kapsula chip (janr, fasl). Bosish uchun Button ichiga o'rang.
struct GlassChip: View {
    let title: String
    var count: Int? = nil
    var isSelected: Bool = false

    var body: some View {
        HStack(spacing: 6) {
            Text(title)
                .font(.subheadline.weight(.semibold))
            if let count = count, count > 0 {
                Text(String(count))
                    .font(.caption2.weight(.bold))
                    .foregroundStyle(isSelected ? Theme.onAccent.opacity(0.7) : Theme.textSecondary)
            }
        }
        .foregroundStyle(isSelected ? Theme.onAccent : Theme.textPrimary)
        .padding(.horizontal, 14)
        .padding(.vertical, 9)
        .glassEffect(chipGlass, in: .capsule)
        .contentShape(Capsule())
    }

    private var chipGlass: Glass {
        if isSelected {
            return Glass.regular.tint(Theme.accent).interactive()
        }
        return Glass.regular.interactive()
    }
}

/// Elementlarni qatorga sig'guncha joylab, keyingi qatorga o'tkazuvchi layout
struct FlowLayout: Layout {
    var spacing: CGFloat = 8
    var lineSpacing: CGFloat = 8

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let maxWidth = proposal.width ?? .infinity
        var x: CGFloat = 0
        var y: CGFloat = 0
        var lineHeight: CGFloat = 0
        var widest: CGFloat = 0

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if x > 0 && x + size.width > maxWidth {
                y += lineHeight + lineSpacing
                x = 0
                lineHeight = 0
            }
            x += size.width
            widest = max(widest, x)
            x += spacing
            lineHeight = max(lineHeight, size.height)
        }

        let width = proposal.width ?? widest
        return CGSize(width: width, height: y + lineHeight)
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        var x = bounds.minX
        var y = bounds.minY
        var lineHeight: CGFloat = 0

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if x > bounds.minX && x + size.width > bounds.maxX {
                y += lineHeight + lineSpacing
                x = bounds.minX
                lineHeight = 0
            }
            subview.place(at: CGPoint(x: x, y: y), anchor: .topLeading, proposal: ProposedViewSize(size))
            x += size.width + spacing
            lineHeight = max(lineHeight, size.height)
        }
    }
}
