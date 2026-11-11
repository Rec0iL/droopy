#version 440
// Default /droopy background (replaced per app in the look phase).
// Uniform contract shared by every droplet - keep the block exactly like this.
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float time;        // accumulated animation time (already speed-scaled in QML)
    vec2 resolution;
    float energy;      // 0 = idle, 1 = excited (dragging / working)
    float quality;     // 1 = full, 0 = low power (skip expensive layers)
    float night;       // 0 = light theme, 1 = dark theme (animated in QML)
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

    vec3 top = mix(vec3(0.86, 0.90, 0.95), vec3(0.05, 0.07, 0.13), night);
    vec3 bot = mix(vec3(0.76, 0.82, 0.92), vec3(0.03, 0.04, 0.08), night);
    vec3 tint = mix(vec3(0.30, 0.50, 0.95), vec3(0.30, 0.60, 1.00), night);

    vec3 col = mix(top, bot, uv.y);
    float n = fbm(p * 1.6 + time * 0.04);
    col = mix(col, tint, n * (0.10 + 0.10 * energy));

    if (quality > 0.5) {
        vec2 g = fract(uv * resolution / 32.0);
        float line = step(g.x, 0.03) + step(g.y, 0.03);
        col = mix(col, tint, clamp(line, 0.0, 1.0) * 0.05);
    }

    col *= 1.0 - (0.22 + 0.15 * night) * dot(p * 0.9, p * 0.9);
    col += (hash(uv * resolution + fract(time)) - 0.5) * 0.02;
    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0) * qt_Opacity;
}
