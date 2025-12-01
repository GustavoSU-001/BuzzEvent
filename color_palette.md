# Color Palette Reference

Based on the provided color palette image, here are the colors for the BuzzEvent interface:

## Color Palette

| Color Name | Hex Code | RGB | Kivy RGBA | Usage |
|------------|----------|-----|-----------|--------|
| Electric Aqua | `#8DECF3` | 141, 236, 243 | `0.553, 0.925, 0.953, 1` | Light accents, backgrounds |
| Pearl Aqua | `#85E6D9` | 133, 230, 217 | `0.522, 0.902, 0.851, 1` | Secondary backgrounds |
| Aquamarine | `#7DDFBE` | 125, 223, 190 | `0.490, 0.875, 0.745, 1` | Tertiary accents |
| Emerald | `#6DD188` | 109, 209, 136 | `0.427, 0.820, 0.533, 1` | Success states, confirmations |
| Mina Green | `#5DC452` | 93, 196, 82 | `0.365, 0.769, 0.322, 1` | Primary actions, buttons |
| Bright Fern | `#56BD37` | 86, 189, 55 | `0.337, 0.741, 0.216, 1` | Highlights, active states |
| Bright Fern (Alt) | `#4D861C` | 77, 134, 28 | `0.302, 0.525, 0.110, 1` | Dark green accents |

## Recommended Application

### Primary Colors
- **Main Actions**: Mina Green (`#5DC452`) - Use for primary buttons like "Crear Evento"
- **Success/Confirmation**: Emerald (`#6DD188`)
- **Hover States**: Bright Fern (`#56BD37`)

### Background Colors
- **Light Backgrounds**: Electric Aqua (`#8DECF3`) or Pearl Aqua (`#85E6D9`)
- **Card/Container Backgrounds**: White with subtle Aquamarine tint

### Accent Colors
- **Labels/Headers**: Bright Fern Alt (`#4D861C`) for contrast
- **Borders**: Aquamarine (`#7DDFBE`)

## Example Kivy Implementation

```kv
# Primary Button
Button:
    background_color: 0.365, 0.769, 0.322, 1  # Mina Green
    color: 1, 1, 1, 1  # White text

# Success Indicator
canvas.before:
    Color:
        rgba: 0.427, 0.820, 0.533, 1  # Emerald
    Rectangle:
        size: self.size
        pos: self.pos

# Light Background
canvas.before:
    Color:
        rgba: 0.553, 0.925, 0.953, 0.3  # Electric Aqua with transparency
```

## Notes
- Use the brighter greens (Mina Green, Bright Fern) for interactive elements
- Use the aqua tones for backgrounds and less prominent elements
- Maintain good contrast for text readability
- Consider using gradients between similar colors for depth
