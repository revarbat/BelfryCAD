# Proposed XML-Based Cad File Format

## Sections

1. Document Settings
    <cad_document>
        - units="Inches"
        - fractions="true"
        - window_geometry="1024x786+150+20"
        - precision="4"
2. Parametrics
    <parameters>
        <param name="length">100</param>
        <param name="width">50</param>
        <param name="half_width">$length/2<param>
    </parameters>
3. Tools Table
    <tooltable>
        <tool
            toolnum="1"
            pocket="3"
            diam="0.375"
            length="2.0"
            flutes="3"
            coating="TiN"
            material="Carbide"
            geometry="square" | "ball" | "vee" | "dovetail" | "fly" | "thread"
            taper="60" (for vee and dovetail)
        >
            3/8 square endmill
        </tool>
    </tooltable>
3. Objects
    1. Common elements
        - id=
        - transform=
    2. CAD specific elements
        - toolnum=1
        - offset_side="left" | "right" | "none"
        - cut_depth=0.25
    3. Object Specific elements
        - <line>
            - start=
            - end=
        - <rect>
            - corner1=
            - corner2=
        - <path>
            - d=
        - <arc>
            - center=
            - radius=
            - start=
            - end=
        - <circle>
            - center=
            - radius=
        - <ngon>
            - center=
            - n=
        - <text>Text</text>
            - pos=
            - halign=
            - valign=
            - font_family=
            - font_size=
        - <image>
            - width=
            - height=
            - src=
        - <spurgear>
            - module= | diam_pitch=
            - center=
            - teeth=
            - pressure_angle=
            - profile_shift=
        - <threadedhole>
            - center=
            - diam=
            - pitch= | tpi=
    4. Grouping
        - <layer>objects</layer>
            - layer_id=
            - name=
            - visible=
            - locked=
            - color=
        - <group>objects</group>


