"""Site tree export service for various formats."""

import csv
import json
import xml.etree.ElementTree as ET
from io import StringIO
from typing import Dict, Any, List, Optional


class SiteTreeExporter:
    """
    Export site trees to various formats.

    Supported formats:
    - JSON (hierarchical and flat)
    - CSV (flat structure)
    - XML (hierarchical)
    - Mermaid (flowchart diagram)
    - HTML (nested lists)
    """

    @staticmethod
    def to_json(tree: Dict[str, Any], pretty: bool = True) -> str:
        """
        Export tree to JSON format.

        Args:
            tree: Tree dictionary
            pretty: Whether to format with indentation

        Returns:
            JSON string
        """
        indent = 2 if pretty else None
        return json.dumps(tree, indent=indent, ensure_ascii=False)

    @staticmethod
    def to_csv(tree: Dict[str, Any]) -> str:
        """
        Export tree to CSV format (flattened).

        Args:
            tree: Tree dictionary

        Returns:
            CSV string
        """
        # Flatten tree
        nodes = SiteTreeExporter._flatten_tree(tree)

        # Create CSV
        output = StringIO()
        if not nodes:
            return ""

        # Define fields
        fieldnames = [
            "level",
            "name",
            "slug",
            "url",
            "keyword",
            "title",
            "meta_description",
            "priority",
            "target_word_count",
            "parent_slug",
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for node in nodes:
            writer.writerow(node)

        return output.getvalue()

    @staticmethod
    def to_xml(tree: Dict[str, Any]) -> str:
        """
        Export tree to XML format.

        Args:
            tree: Tree dictionary

        Returns:
            XML string
        """
        root = ET.Element("sitetree")

        def build_xml_node(parent_element: ET.Element, node_data: Dict[str, Any]):
            """Recursively build XML tree."""
            node_element = ET.SubElement(parent_element, "node")

            # Add node attributes
            for key, value in node_data.items():
                if key != "children" and value is not None:
                    child_elem = ET.SubElement(node_element, key)
                    child_elem.text = str(value)

            # Process children
            if "children" in node_data and node_data["children"]:
                children_elem = ET.SubElement(node_element, "children")
                for child in node_data["children"]:
                    build_xml_node(children_elem, child)

        build_xml_node(root, tree)

        # Convert to string with declaration
        xml_str = ET.tostring(root, encoding="unicode", method="xml")
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'

    @staticmethod
    def to_mermaid(tree: Dict[str, Any]) -> str:
        """
        Export tree to Mermaid flowchart format.

        Args:
            tree: Tree dictionary

        Returns:
            Mermaid diagram code
        """
        lines = ["flowchart TD"]
        node_counter = [0]  # Use list to allow mutation in nested function

        def get_node_id(name: str) -> str:
            """Generate unique node ID."""
            node_counter[0] += 1
            # Sanitize name for Mermaid
            safe_name = name.replace(" ", "_").replace("-", "_")
            return f"node{node_counter[0]}_{safe_name}"

        def build_mermaid_node(
            node_data: Dict[str, Any], parent_id: Optional[str] = None
        ):
            """Recursively build Mermaid nodes."""
            node_name = node_data.get("name", "Untitled")
            node_id = get_node_id(node_name)

            # Create node with label
            slug = node_data.get("slug", "")
            priority = node_data.get("priority", "medium")

            # Style based on priority
            if priority == "critical":
                shape_start, shape_end = "[[", "]]"  # Double bracket for critical
            elif priority == "high":
                shape_start, shape_end = "[", "]"  # Square for high
            else:
                shape_start, shape_end = "(", ")"  # Round for medium/low

            label = f"{node_name}<br/>{slug}"
            lines.append(f'    {node_id}{shape_start}"{label}"{shape_end}')

            # Add connection from parent
            if parent_id:
                lines.append(f"    {parent_id} --> {node_id}")

            # Process children
            if "children" in node_data and node_data["children"]:
                for child in node_data["children"]:
                    build_mermaid_node(child, node_id)

        build_mermaid_node(tree)

        # Add style classes
        lines.append("")
        lines.append("    classDef critical fill:#ff6b6b")
        lines.append("    classDef high fill:#ffd93d")
        lines.append("    classDef medium fill:#6bcf7f")

        return "\n".join(lines)

    @staticmethod
    def to_html(tree: Dict[str, Any]) -> str:
        """
        Export tree to HTML nested list format.

        Args:
            tree: Tree dictionary

        Returns:
            HTML string
        """
        lines = ['<!DOCTYPE html>', '<html>', '<head>', '<meta charset="UTF-8">']
        lines.append("<title>Site Tree</title>")
        lines.append("<style>")
        lines.append("  body { font-family: Arial, sans-serif; padding: 20px; }")
        lines.append("  ul { list-style-type: none; padding-left: 20px; }")
        lines.append("  li { margin: 10px 0; }")
        lines.append("  .node { padding: 5px; border-left: 3px solid #ccc; }")
        lines.append("  .critical { border-left-color: #ff6b6b; }")
        lines.append("  .high { border-left-color: #ffd93d; }")
        lines.append("  .medium { border-left-color: #6bcf7f; }")
        lines.append("  .name { font-weight: bold; font-size: 1.1em; }")
        lines.append("  .slug { color: #666; font-size: 0.9em; }")
        lines.append("  .meta { color: #999; font-size: 0.85em; margin-top: 3px; }")
        lines.append("</style>")
        lines.append("</head>")
        lines.append("<body>")
        lines.append("<h1>Site Architecture Tree</h1>")

        def build_html_node(node_data: Dict[str, Any]) -> str:
            """Recursively build HTML list."""
            name = node_data.get("name", "Untitled")
            slug = node_data.get("slug", "")
            keyword = node_data.get("keyword", "")
            priority = node_data.get("priority", "medium")
            meta_desc = node_data.get("meta_description", "")

            html_parts = ['<li>']
            html_parts.append(f'<div class="node {priority}">')
            html_parts.append(f'<div class="name">{name}</div>')
            html_parts.append(f'<div class="slug">{slug}</div>')

            if keyword or meta_desc:
                html_parts.append('<div class="meta">')
                if keyword:
                    html_parts.append(f'<strong>Keyword:</strong> {keyword} ')
                if meta_desc:
                    truncated = (
                        meta_desc[:100] + "..." if len(meta_desc) > 100 else meta_desc
                    )
                    html_parts.append(f'<br/><strong>Meta:</strong> {truncated}')
                html_parts.append("</div>")

            html_parts.append("</div>")

            # Process children
            if "children" in node_data and node_data["children"]:
                html_parts.append("<ul>")
                for child in node_data["children"]:
                    html_parts.append(build_html_node(child))
                html_parts.append("</ul>")

            html_parts.append("</li>")
            return "".join(html_parts)

        lines.append("<ul>")
        lines.append(build_html_node(tree))
        lines.append("</ul>")
        lines.append("</body>")
        lines.append("</html>")

        return "\n".join(lines)

    @staticmethod
    def to_sitemap_xml(tree: Dict[str, Any], base_url: str) -> str:
        """
        Export tree as XML sitemap format.

        Args:
            tree: Tree dictionary
            base_url: Base URL of the site (e.g., "https://example.com")

        Returns:
            XML sitemap string
        """
        # Remove trailing slash from base_url
        base_url = base_url.rstrip("/")

        # Flatten tree
        nodes = SiteTreeExporter._flatten_tree(tree)

        # Create sitemap XML
        urlset = ET.Element(
            "urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        )

        for node in nodes:
            url_element = ET.SubElement(urlset, "url")

            # Construct full URL
            slug = node.get("slug", "").lstrip("/")
            full_url = f"{base_url}/{slug}" if slug else base_url

            loc = ET.SubElement(url_element, "loc")
            loc.text = full_url

            # Priority based on level
            priority_val = node.get("priority", "medium")
            priority_map = {"critical": "1.0", "high": "0.8", "medium": "0.6", "low": "0.4"}
            priority = ET.SubElement(url_element, "priority")
            priority.text = priority_map.get(priority_val, "0.5")

            # Change frequency based on level
            level = node.get("level", 0)
            changefreq = ET.SubElement(url_element, "changefreq")
            if level == 0:
                changefreq.text = "daily"
            elif level == 1:
                changefreq.text = "weekly"
            else:
                changefreq.text = "monthly"

        xml_str = ET.tostring(urlset, encoding="unicode", method="xml")
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'

    @staticmethod
    def _flatten_tree(
        tree: Dict[str, Any], parent_slug: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Flatten hierarchical tree into list of nodes.

        Args:
            tree: Tree dictionary
            parent_slug: Slug of parent node

        Returns:
            List of flattened nodes
        """
        nodes = []

        node_copy = tree.copy()
        children = node_copy.pop("children", [])

        node_copy["parent_slug"] = parent_slug
        nodes.append(node_copy)

        for child in children:
            nodes.extend(SiteTreeExporter._flatten_tree(child, node_copy.get("slug")))

        return nodes
