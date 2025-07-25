
setup(
    material="Aluminum 6061",  // Gets Surface Feed per Minute for 6061 aluminum.
    sfm=20,  // Override SFM because we think we know better.
    units="mm",
    size=[50,50,5]
);

module sinewave(size) {
    path = [for (a = [0:5:360]) [a / 360 * size.x - size.x/2, sin(a) * size.y/2]];
    stroke(path);
}

module rrect(size, r) {
    midlenx = size.x - 2 * r;
    midleny = size.y - 2 * r;
    hull() {
        for (x=[-1,1],y=[-1,1]) translate([x,y]) circle(r=r);
    }
}

pocket(tool=3, depth=3) {
    rrect([30,30],r=10),
    circle(r=10);
}

cut(tool=2, depth=1, side="center")
    line([-20,-20], [20,20]);

cut(tool=2, depth=2, side="left")
    sinewave([40,40]);

pocket(tool=2, depth=5)
    circle(d=0.25);

spiralcut(tool=1, depth=4, diam=6, spacing=1);


