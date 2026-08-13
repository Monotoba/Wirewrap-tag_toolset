// Parametric Wire-Wrap Socket ID Tag
// Units: mm

pins = 16;                 // even DIP pin count
row_spacing_mil = 300;     // standard choices: 300, 400, 600, 900
thickness = 0.8;           // 0.6 to 1.0 mm recommended
pin_pitch = 2.54;          // DIP standard 0.100 in
hole_diameter = 1.15;      // tune for printer/material/post fit
end_margin = 2.3;          // plastic beyond first/last pin centers
side_margin = 2.0;         // plastic outside pin rows
notch_radius = 2.0;        // semicircular pin-1-end notch radius
corner_radius = 0.8;
center_window = false;     // optional center opening; labels normally cover solid tag
center_window_margin = 1.5;

function mil_to_mm(m) = m * 0.0254;
rows = pins / 2;
row_spacing = mil_to_mm(row_spacing_mil);
length = (rows - 1) * pin_pitch + 2 * end_margin;
width = row_spacing + 2 * side_margin;

module rounded_rect_2d(x, y, r) {
    hull() {
        for (sx=[-1,1], sy=[-1,1])
            translate([sx*(x/2-r), sy*(y/2-r)]) circle(r=r, $fn=32);
    }
}

module tag_2d() {
    difference() {
        rounded_rect_2d(length, width, corner_radius);

        // pin holes, viewed from the component/tag side.
        // Physical numbering follows DIP convention: pin 1 at upper-left
        // when the notch is at the left end; pin numbers increase CCW.
        for (i=[0:rows-1]) {
            x = -length/2 + end_margin + i*pin_pitch;
            translate([x, -row_spacing/2]) circle(d=hole_diameter, $fn=28);
            translate([x,  row_spacing/2]) circle(d=hole_diameter, $fn=28);
        }

        // orientation notch on pin-1 end (left end)
        translate([-length/2, 0]) circle(r=notch_radius, $fn=48);

        if (center_window) {
            window_len = max(1, length - 2*(end_margin + center_window_margin));
            window_wid = max(1, row_spacing - 2*center_window_margin);
            square([window_len, window_wid], center=true);
        }
    }
}

linear_extrude(height=thickness) tag_2d();
