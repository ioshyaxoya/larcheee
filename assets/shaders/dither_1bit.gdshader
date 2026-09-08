shader_type canvas_item;
render_mode unshaded;
// Режим испытания (docs/visual_direction.md §4): время стоит — цвета нет.
// Монохром с упорядоченным дизерингом; `colour_return` 0→1 возвращает цвет
// по выигранным раундам. Золотая вспышка на повороте стрелки — поверх, в UI.

// Кадр мира приходит текстурой прямоугольника: интерфейс рисуется поверх и не дизерится.
uniform float colour_return : hint_range(0.0, 1.0) = 0.0;
uniform vec3 tint = vec3(1.0, 1.0, 1.0);
uniform float saturation : hint_range(0.0, 2.0) = 1.0;
uniform float pixel_size : hint_range(1.0, 6.0) = 2.0;
uniform vec3 ink = vec3(0.04, 0.04, 0.06);
uniform vec3 paper = vec3(0.86, 0.85, 0.80);
uniform float vignette : hint_range(0.0, 1.0) = 0.35;
// Сбой мира: присутствие сомневается во всём вокруг, и сквозь его мир полосами
// проступает вагон — тем же точечным растром, каким нарисован мир.
uniform sampler2D alt_tex : hint_default_black, filter_linear;
uniform float glitch : hint_range(0.0, 1.0) = 0.0;
uniform float time = 0.0;

float hash1(float x) {
	return fract(sin(x * 91.7351) * 43758.5453);
}

const vec3 LUMA = vec3(0.2126, 0.7152, 0.0722);

// Матрица Байера 4×4 без массивов: два вложенных порядка 2×2.
float bayer2(vec2 a) {
	a = floor(a);
	return fract(a.x / 2.0 + a.y * a.y * 0.75);
}

float bayer4(vec2 a) {
	return bayer2(0.5 * a) * 0.25 + bayer2(a);
}

void fragment() {
	vec2 uv = UV;
	vec3 c = texture(TEXTURE, uv).rgb;

	// Полосы сбоя: широкие, редкие, со сдвигом по горизонтали — разрыв ткани
	// мира, а не рябь помех. Вагон в них виден целиком, поэтому берётся кадр.
	if (glitch > 0.001) {
		// Вспышками: чаще всего мир держится, и тем страшнее, когда рвётся.
		float beat = floor(time * 1.6);
		float burst = smoothstep(0.60, 0.95, hash1(beat * 5.3 + 2.0));
		float g = glitch * mix(burst, 1.0, smoothstep(0.80, 1.0, glitch));
		float row = floor(uv.y * 46.0);
		float pick = hash1(row + beat * 7.0);
		float band = step(1.0 - g * 0.42, pick);
		float shift = (hash1(row * 3.1 + 11.0) - 0.5) * 0.05 * g;
		vec2 uv2 = clamp(uv + vec2(shift, 0.0), vec2(0.001), vec2(0.999));
		vec3 alt = texture(alt_tex, uv2).rgb;
		c = mix(c, alt, band);
	}

	float l = dot(c, LUMA);

	float threshold = bayer4(FRAGCOORD.xy / pixel_size);
	// Гамма-подтяжка: в тенях дизеринг не съедает деталь целиком.
	float lit = step(threshold, pow(l, 0.85));
	vec3 mono = mix(ink, paper, lit);

	vec3 colour = mix(vec3(l), c, saturation) * tint;
	vec3 outc = mix(mono, colour, colour_return);

	vec2 d = uv - vec2(0.5);
	outc *= clamp(1.0 - vignette * dot(d, d) * 2.6, 0.0, 1.0);

	COLOR = vec4(clamp(outc, vec3(0.0), vec3(1.0)), 1.0);
}
