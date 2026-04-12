import math
from aho.council.status import CouncilStatus
from aho.dashboard.lego.palette import COLOR_OPERATIONAL, COLOR_GAP, COLOR_UNKNOWN, COLOR_BG, COLOR_TEXT, COLOR_STROKE, COLOR_LINE
from aho.dashboard.lego.layout import get_node_position, get_relationships, BLOCK_W, BLOCK_H

def render_council_svg(status: CouncilStatus) -> str:
    """Render the council status into a static SVG document."""
    width = 1500
    height = 1100

    svg_elements = []
    svg_elements.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">')
    svg_elements.append(f'<rect width="{width}" height="{height}" fill="{COLOR_BG}"/>')
    
    # Optional grid/office lines for aesthetics
    svg_elements.append(f'<text x="50" y="40" fill="{COLOR_TEXT}" font-family="sans-serif" font-size="24" font-weight="bold">aho Council Operations (0.2.12)</text>')

    # Map members to nodes
    nodes = {}
    for member in status.members:
        x, y = get_node_position(member.name, member.kind)
        
        # Color encoding based on status text
        color = COLOR_UNKNOWN
        if "operational" in member.status.lower():
            color = COLOR_OPERATIONAL
        elif "gap" in member.status.lower():
            color = COLOR_GAP
            
        nodes[member.name] = {
            "name": member.name,
            "kind": member.kind,
            "status": member.status,
            "color": color,
            "x": x,
            "y": y
        }

    # Render relationships (lines)
    for src_substr, tgt_substr, confirmed in get_relationships():
        src_node = next((v for k, v in nodes.items() if src_substr in k.lower()), None)
        tgt_node = next((v for k, v in nodes.items() if tgt_substr in k.lower()), None)
        
        if src_node and tgt_node:
            sx, sy = src_node["x"] + BLOCK_W // 2, src_node["y"]
            tx, ty = tgt_node["x"] - BLOCK_W // 2, tgt_node["y"]
            
            line_color = src_node["color"]
            stroke_dash = "" if confirmed else 'stroke-dasharray="5,5"'
            
            # Simple straight or curved line
            # Path data: M sx,sy C sx+100,sy tx-100,ty tx,ty
            path_d = f"M {sx},{sy} C {sx+100},{sy} {tx-100},{ty} {tx},{ty}"
            
            svg_elements.append(f'<path d="{path_d}" fill="none" stroke="{line_color}" stroke-width="3" {stroke_dash} />')
            
    # Render nodes (figures/desks)
    for name, node in nodes.items():
        nx = node["x"] - BLOCK_W // 2
        ny = node["y"] - BLOCK_H // 2
        color = node["color"]
        
        # Figure rect
        svg_elements.append(f'<rect x="{nx}" y="{ny}" width="{BLOCK_W}" height="{BLOCK_H}" rx="8" fill="{color}" stroke="{COLOR_STROKE}" stroke-width="2"/>')
        
        # Label
        # Clip long names
        display_name = name[:20] + "..." if len(name) > 23 else name
        svg_elements.append(f'<text x="{nx + 10}" y="{ny + 25}" fill="{COLOR_BG}" font-family="sans-serif" font-size="14" font-weight="bold">{display_name}</text>')
        
        # Tooltip content (gap text if any)
        status_text = node["status"].replace('"', "'")[:40]
        if len(node["status"]) > 40:
            status_text += "..."
        svg_elements.append(f'<text x="{nx + 10}" y="{ny + 45}" fill="{COLOR_BG}" font-family="sans-serif" font-size="10">{status_text}</text>')
        
        # Tooltip standard SVG trick (title element inside rect)
        # However, text inside rect isn't strictly valid. We wrap in a group.
        # Actually it's better to just leave it as text elements for now.

    svg_elements.append('</svg>')
    return "\\n".join(svg_elements)
