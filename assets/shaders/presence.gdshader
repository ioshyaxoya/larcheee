shader_type canvas_item;
render_mode unshaded;
// Присутствие поверх дизеренного мира. Оно не грейдится в монохром — но и не
// наклеено: тот же виньеточный спад, что у мира, и лёгкий подъём насыщенности,
// чтобы глазурь не гасла к краям кадра. Без этого фигура выглядит вырезкой,
// положенной на фон, и всю работу видно.
uniform float vignette : hint_range(0.0, 1.0) = 0.35;
uniform float saturation : hint_range(0.0, 2.0) = 1.06;
uniform vec3 ambient = vec3(0.62, 0.66, 0.74);   // холодный свет мира Шани
uniform float ambient_mix : hint_range(0.0, 1.0) = 0.10;

const vec3 LUMA = vec3(0.2126, 0.7152, 0.0722);

void fragment() {
	vec4 c = texture(TEXTURE, UV);
	if (c.a < 0.004) {
		COLOR = vec4(0.0);
	} else {
		vec3 rgb = c.rgb / max(c.a, 0.004);
		float l = dot(rgb, LUMA);
		rgb = mix(vec3(l), rgb, saturation);
		// Свет сцены ложится и на присутствие: иначе оно из другой картинки.
		rgb = mix(rgb, rgb * ambient, ambient_mix);
		vec2 d = UV - vec2(0.5);
		rgb *= clamp(1.0 - vignette * dot(d, d) * 2.6, 0.0, 1.0);
		COLOR = vec4(clamp(rgb, vec3(0.0), vec3(1.0)) * c.a, c.a);
	}
}
