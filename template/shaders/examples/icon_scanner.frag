#version 440
// "Resource scanner" background: a faint pixel grid on slate, bitmap cells that
// light up as a scan line sweeps over them (an icon being decoded out of a
// binary), drifting data-flow columns, vignette and a touch of grain.
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float time;        // accumulated animation time (already speed-scaled in QML)
    vec2 resolution;
    float energy;      // 0 = idle, 1 = excited (dragging / extracting)
    float quality;     // 1 = full, 0 = low power (skips the extra layers)
    float night;       // 0 = light, 1 = dark (animated in QML)
};

float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float noise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x),
               mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}

void main() {
    vec2 uv = qt_TexCoord0;
    vec2 px = uv * resolution;                 // pixel coordinates
    float asp = resolution.x / resolution.y;
    vec2 p = (uv - 0.5) * vec2(asp, 1.0);

    // ---- palettes (light "graph paper" <-> dark slate), cross-faded by `night`
    vec3 bgTop = mix(vec3(0.90, 0.93, 0.98), vec3(0.075, 0.095, 0.150), night);
    vec3 bgBot = mix(vec3(0.80, 0.86, 0.95), vec3(0.040, 0.055, 0.100), night);
    vec3 gridC = mix(vec3(0.55, 0.65, 0.85), vec3(0.30, 0.45, 0.70), night);
    vec3 cyan  = mix(vec3(0.15, 0.55, 0.95), vec3(0.30, 0.85, 1.00), night);
    vec3 blue  = mix(vec3(0.30, 0.45, 0.95), vec3(0.35, 0.55, 1.00), night);
    vec3 amber = mix(vec3(0.95, 0.60, 0.15), vec3(1.00, 0.72, 0.30), night);

    vec3 col = mix(bgTop, bgBot, uv.y);
    // soft cloudy depth so the slate is not flat
    col += (noise(p * 2.5 + time * 0.03) - 0.5) * mix(0.05, 0.06, night);

    // ---- pixel grid -----------------------------------------------------------
    float cell = 28.0;                              // grid cell size in pixels
    vec2 g = px / cell;
    vec2 gf = fract(g);
    vec2 gid = floor(g);
    float lineW = 1.0 / cell;
    float line = step(gf.x, lineW) + step(gf.y, lineW);
    float major = step(fract(g.x / 8.0), lineW / 8.0) + step(fract(g.y / 8.0), lineW / 8.0);
    col = mix(col, gridC, clamp(line, 0.0, 1.0) * mix(0.10, 0.08, night));
    col = mix(col, gridC, clamp(major, 0.0, 1.0) * mix(0.14, 0.14, night));

    // ---- scan line (the "reader") ---------------------------------------------
    float period = 7.0 - 3.5 * energy;
    float scanY = fract(time / period);             // 0..1 top -> bottom
    float dy = uv.y - scanY;
    float head = exp(-abs(dy) * resolution.y * 0.35);             // thin bright line
    float trail = exp(-max(dy, 0.0) * 9.0) * step(0.0, dy);       // glow behind it
    float recent = exp(-max(dy, 0.0) * 2.2) * step(0.0, dy);      // cells stay lit a while

    // ---- bitmap cells being decoded -------------------------------------------
    float h = hash(gid + floor(time / (period * 4.0)) * 17.0);    // reshuffle every few sweeps
    float lit = step(0.80 - 0.10 * energy, h);                    // sparse set of cells
    vec2 inner = abs(gf - 0.5);
    float square = step(max(inner.x, inner.y), 0.36);             // cell body (with gap)
    float cellOn = lit * square * recent;
    float h2 = hash(gid + 3.7);
    vec3 cellC = h2 < 0.55 ? cyan : (h2 < 0.85 ? blue : amber);
    float flicker = 0.75 + 0.25 * sin(time * (3.0 + h * 4.0) + h * 6.28);
    col += cellC * cellOn * flicker * (0.55 + 0.45 * energy) * mix(0.9, 1.0, night);
    // faint ghost of the whole bitmap, so the pattern is readable before the scan
    col += cellC * lit * square * mix(0.035, 0.05, night) * (1.0 + energy);

    // scan line itself
    col += cyan * head * (0.9 + 0.6 * energy);
    col += cyan * trail * mix(0.08, 0.12, night) * (1.0 + energy);

    // ---- data-flow columns (bytes streaming upward) ---------------------------
    if (quality > 0.5) {
        for (int layer = 0; layer < 2; layer++) {
            float fl = float(layer);
            float colsN = 14.0 + 10.0 * fl;
            float cx = floor(uv.x * asp * colsN);
            float speed = 0.05 + 0.04 * fl + hash(vec2(cx, fl)) * 0.05;
            float y = uv.y + time * speed * (1.0 + energy);
            float seg = fract(y * (6.0 + 3.0 * fl));
            float id = floor(y * (6.0 + 3.0 * fl));
            float on = step(0.86, hash(vec2(cx + fl * 99.0, id)));
            float bead = smoothstep(0.0, 0.15, seg) * smoothstep(0.45, 0.30, seg);
            float xin = smoothstep(0.0, 0.2, fract(uv.x * asp * colsN)) *
                        smoothstep(1.0, 0.8, fract(uv.x * asp * colsN));
            col += mix(blue, cyan, fl) * on * bead * xin * mix(0.06, 0.10, night) * (0.6 + 0.6 * energy);
        }
    }

    // excitement: lift everything slightly
    col = mix(col, col * 1.08 + cyan * 0.03, energy);

    // vignette + grain
    col *= 1.0 - (0.22 + 0.18 * night) * dot(p * 0.9, p * 0.9);
    col += (hash(uv * resolution + fract(time)) - 0.5) * 0.02;

    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0) * qt_Opacity;
}
