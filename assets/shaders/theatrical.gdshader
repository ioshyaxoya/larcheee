shader_type canvas_item;
render_mode unshaded;
// Базовый режим (docs/visual_direction.md §3): плоскости в объёме, лужи света
// в темноте, грейдинг по car.palette (A10). Свет делает работу — шейдер только
// доводит цвет, кадрирует виньеткой и добавляет плёночное зерно.

// Кадр мира приходит текстурой прямоугольника: интерфейс рисуется поверх и не грейдится.
uniform vec3 tint = vec3(1.0, 1.0, 1.0);
uniform float saturation : hint_range(0.0, 2.0) = 1.0;
uniform float contrast : hint_range(0.5, 2.0) = 1.0;
uniform float brightness : hint_range(0.2, 2.0) = 1.0;
uniform float vignette : hint_range(0.0, 1.0) = 0.3;
uniform float grain : hint_range(0.0, 0.2) = 0.03;
uniform float glow : hint_range(0.0, 1.0) = 0.0;
uniform float seed = 0.0;

const vec3 LUMA = vec3(0.2126, 0.7152, 0.0722);

void fragment() {
	vec2 uv = UV;
	vec3 c = texture(TEXTURE, uv).rgb;

	// Сияние: болливудский контровой свет по ярким местам, без размытия по кадру.
	if (glow > 0.0) {
		vec2 px = 1.5 / vec2(textureSize(TEXTURE, 0));
		vec3 halo = texture(TEXTURE, uv + vec2(px.x, 0.0)).rgb
			+ texture(TEXTURE, uv - vec2(px.x, 0.0)).rgb
			+ texture(TEXTURE, uv + vec2(0.0, px.y)).rgb
			+ texture(TEXTURE, uv - vec2(0.0, px.y)).rgb;
		halo *= 0.25;
		float l = dot(halo, LUMA);
		c += halo * smoothstep(0.35, 0.9, l) * glow;
	}

	c *= brightness;
	c = (c - 0.5) * contrast + 0.5;
	c = mix(vec3(dot(c, LUMA)), c, saturation);
	c *= tint;

	// Виньетка: кулисы. Кадр театральный, края уходят в тень.
	vec2 d = uv - vec2(0.5);
	c *= clamp(1.0 - vignette * dot(d, d) * 2.6, 0.0, 1.0);

	float n = fract(sin(dot(uv * vec2(1927.0, 3271.0) + seed, vec2(12.9898, 78.233))) * 43758.5453);
	c += (n - 0.5) * grain;

	COLOR = vec4(clamp(c, vec3(0.0), vec3(1.0)), 1.0);
}
