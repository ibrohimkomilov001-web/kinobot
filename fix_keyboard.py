# -*- coding: utf-8 -*-

with open('keyboards.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 173-191 qatorlarni almashtirish
new_lines = []
skip_range = False

for i, line in enumerate(lines):
    line_num = i + 1
    
    if line_num == 173:
        # Yangi funksiya
        new_lines.append('def channel_button_settings_keyboard(is_enabled: bool):\n')
        new_lines.append('    """Kanal tugmasi sozlamalari"""\n')
        new_lines.append('    toggle_text = "🔴 O\'chirish" if is_enabled else "🟢 Yoqish"\n')
        new_lines.append('    \n')
        new_lines.append('    keyboard = InlineKeyboardMarkup(\n')
        new_lines.append('        inline_keyboard=[\n')
        new_lines.append('            [\n')
        new_lines.append('                InlineKeyboardButton(text=toggle_text, callback_data="channel_btn_toggle")\n')
        new_lines.append('            ],\n')
        new_lines.append('            [\n')
        new_lines.append('                InlineKeyboardButton(text="✏️ Matnni tahrirlash", callback_data="channel_btn_edit_text"),\n')
        new_lines.append('                InlineKeyboardButton(text="🔗 Linkni tahrirlash", callback_data="channel_btn_edit_url")\n')
        new_lines.append('            ],\n')
        new_lines.append('            [\n')
        new_lines.append('                InlineKeyboardButton(text="🔙 Orqaga", callback_data="movie_management")\n')
        new_lines.append('            ]\n')
        new_lines.append('        ]\n')
        new_lines.append('    )\n')
        new_lines.append('    return keyboard\n')
        skip_range = True
        continue
    
    if skip_range and line_num <= 191:
        continue
    else:
        skip_range = False
        new_lines.append(line)

with open('keyboards.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Keyboard yangilandi!')
