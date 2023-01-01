#version 450

layout(location = 0) in vec2 uv;

layout(binding = 0) uniform sampler2D texSampler;

layout(location = 0) out vec4 outColor;

void main(){
	float vignette = min(distance(vec2(0.5, 0.5), uv), 1);
	vignette = vignette * 1.5 - 0.5;
	vignette = smoothstep(0, 1, vignette);
	outColor = mix(texture(texSampler, uv), vec4(0,0,0,1), vignette);
}