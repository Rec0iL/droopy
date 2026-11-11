#version 440
// Dreamy pastel background: domain-warped gradient, soft aurora ribbons,
// twinkling stars, floating bokeh, vignette and a touch of film grain.
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float time;        // accumulated animation time (already speed-scaled in QML)
    vec2 resolution;
    float energy;      // 0 = calm, 1 = excited (dragging / converting)
    float quality;     // 1 = full, 0 = low power (skips stars/bokeh)
    float night;       // 0 = pastel day, 1 = dreamy night (animated in QML)
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

float fbm(vec2 p) {
    float v = 0.0, a = 0.5;
    for (int i = 0; i < 4; i++) {
        v += a * noise(p);
        p = p * 2.02 + vec2(17.1, 3.7);
        a *= 0.5;
    }
    return v;
}

void main() {
    vec2 uv = qt_TexCoord0;
    float asp = resolution.x / resolution.y;
    vec2 p = (uv - 0.5) * vec2(asp, 1.0);
    float t = time * 0.12;

    // day / night palettes, cross-faded by `night`
    vec3 lavender = mix(vec3(0.60, 0.52, 0.98), vec3(0.10, 0.07, 0.27), night);
    vec3 pink     = mix(vec3(1.00, 0.56, 0.78), vec3(0.36, 0.12, 0.46), night);
    vec3 peach    = mix(vec3(1.00, 0.78, 0.62), vec3(0.55, 0.15, 0.45), night);
    vec3 mint     = mix(vec3(0.56, 0.90, 0.86), vec3(0.08, 0.30, 0.46), night);

    // domain warped noise field
    vec2 q = vec2(fbm(p * 1.4 + t * 0.6), fbm(p * 1.4 + vec2(5.2, 1.3) - t * 0.5));
    float r = fbm(p * 1.1 + 2.0 * q + vec2(t * 0.3, -t * 0.2));

    vec3 col = mix(lavender, pink, smoothstep(0.25, 0.80, r));
    col = mix(col, peach, smoothstep(0.55, 1.0, q.x) * 0.65);
    col = mix(col, mint, smoothstep(0.62, 0.95, q.y) * 0.40);

    // aurora ribbons
    float band = 0.5 + 0.5 * sin(p.x * 2.2 + q.y * 5.0 + time * 0.35);
    float ribbon = pow(band, 5.0) * smoothstep(0.9, 0.1, abs(p.y + 0.15 * sin(p.x * 1.5 + time * 0.2)));
    col += mix(vec3(1.0, 0.95, 1.0), vec3(0.55, 0.85, 1.0), night) * ribbon * (0.13 + 0.10 * energy + 0.10 * night);

    // stars drifting upward + bokeh
    if (quality > 0.5) {
        for (int layer = 0; layer < 2; layer++) {
            float fl = float(layer);
            vec2 g = p * (9.0 + 7.0 * fl) + vec2(0.0, -time * (0.06 + 0.04 * fl));
            vec2 id = floor(g);
            vec2 f = fract(g) - 0.5;
            float h = hash(id + fl * 31.0);
            vec2 pos = (vec2(hash(id + 1.7), hash(id + 9.2)) - 0.5) * 0.6;
            vec2 d = f - pos;
            float tw = 0.5 + 0.5 * sin(time * (0.8 + h * 2.5) + h * 6.2831);
            float core = exp(-dot(d, d) * (900.0 - 300.0 * fl));
            float cross = exp(-abs(d.x) * 90.0) * exp(-abs(d.y) * 14.0)
                        + exp(-abs(d.y) * 90.0) * exp(-abs(d.x) * 14.0);
            float on = step(0.72 - 0.1 * energy, h);
            col += vec3(1.0, 0.97, 1.0) * (core + 0.35 * cross) * tw * on * (0.9 + 0.6 * energy + 0.7 * night);
        }
        // large soft bokeh circles
        vec2 b = p * 3.0 + vec2(0.0, -time * 0.03);
        vec2 bid = floor(b);
        vec2 bf = fract(b) - 0.5;
        float bh = hash(bid + 77.0);
        vec2 bp = (vec2(hash(bid + 3.1), hash(bid + 8.8)) - 0.5) * 0.5;
        float bd = length(bf - bp);
        float rad = 0.10 + 0.10 * bh;
        float bokeh = smoothstep(rad, rad - 0.06, bd) * step(0.62, bh) * 0.10;
        bokeh += smoothstep(0.012, 0.0, abs(bd - rad)) * step(0.62, bh) * 0.10;
        col += mix(vec3(1.0, 0.92, 0.98), vec3(0.75, 0.45, 1.0), night) * bokeh * (1.0 + 0.8 * night);
    }

    // excitement: brighter, slightly warmer
    col = mix(col, col * 1.10 + vec3(0.05, 0.015, 0.06), energy);

    // vignette + grain
    col *= 1.0 - (0.28 + 0.2 * night) * dot(p * 0.9, p * 0.9);
    col += (hash(uv * resolution + fract(time)) - 0.5) * 0.025;

    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0) * qt_Opacity;
}
