import webcolors
import math

# Common color names and their hex values
COLOR_NAMES = {
    '#000000': 'Black',
    '#ffffff': 'White',
    '#ff0000': 'Red',
    '#00ff00': 'Green',
    '#0000ff': 'Blue',
    '#ffff00': 'Yellow',
    '#00ffff': 'Cyan',
    '#ff00ff': 'Magenta',
    '#808080': 'Gray',
    '#800000': 'Maroon',
    '#808000': 'Olive',
    '#008000': 'Dark Green',
    '#800080': 'Purple',
    '#008080': 'Teal',
    '#000080': 'Navy',
    '#ffa500': 'Orange',
    '#a52a2a': 'Brown',
    '#ffc0cb': 'Pink',
    '#f5f5dc': 'Beige',
    '#e6e6fa': 'Lavender',
    '#d3d3d3': 'Light Gray',
    '#a9a9a9': 'Dark Gray',
    '#add8e6': 'Light Blue',
    '#90ee90': 'Light Green',
    '#ffb6c1': 'Light Pink',
    '#800020': 'Burgundy',
    '#ff7f50': 'Coral',
    '#f0e68c': 'Khaki',
    '#dda0dd': 'Plum',
    '#b0c4de': 'Steel Blue'
}

def hex_to_color_name(hex_code):
    """
    Convert hex color code to the closest named color.
    
    Args:
        hex_code (str): Hex color code, with or without '#' prefix
    
    Returns:
        str: Named color, or the original hex code if conversion fails
    """
    # If None or empty, return empty string
    if not hex_code:
        return ""
    
    # Clean the hex code
    if hex_code.startswith('#'):
        clean_hex = hex_code.lower()
    else:
        clean_hex = f'#{hex_code.lower()}'
    
    # Ensure hex code is properly formatted
    if len(clean_hex) != 7 or not all(c in '0123456789abcdef#' for c in clean_hex):
        # If not a valid hex code, just return it as is without the #
        return hex_code.replace('#', '')
    
    try:
        # Try to get exact color name using webcolors
        try:
            color_name = webcolors.hex_to_name(clean_hex, spec='css3')
            return color_name.replace('-', ' ').title()
        except (ValueError, AttributeError):
            # If exact match fails, check our custom dictionary
            if clean_hex in COLOR_NAMES:
                return COLOR_NAMES[clean_hex]
            
            # Find closest color by RGB distance
            rgb = webcolors.hex_to_rgb(clean_hex)
            min_distance = float('inf')
            closest_color = hex_code.replace('#', '')
            
            # Loop through our custom color dictionary
            for hex_value, name in COLOR_NAMES.items():
                try:
                    color_rgb = webcolors.hex_to_rgb(hex_value)
                    # Calculate Euclidean distance
                    distance = math.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(rgb, color_rgb)))
                    
                    if distance < min_distance:
                        min_distance = distance
                        closest_color = name
                except Exception:
                    continue
            
            return closest_color
    
    except Exception as e:
        # If any error occurs, return the original hex code without #
        print(f"Color conversion error: {e}")
        return hex_code.replace('#', '')
