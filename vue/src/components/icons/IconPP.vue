<template>
	<svg viewBox="0 0 96 96">
		<polygon class="face face-1" points="44.01 47.79 53.83 3.56 38.72 5.22 44.01 47.79"/>
		<polygon class="face face-2" points="45.01 45.87 35.18 90.11 51.54 88.35 45.01 45.87"/>
		<polygon class="face face-3" points="45.01 45.87 16.95 91.87 35.18 90.05 45.01 45.87"/>
		<polygon class="face face-4" points="43.61 47.79 71.65 1.79 53.42 3.61 43.61 47.79"/>
		<polygon class="face face-5" points="60.74 28.39 0 93.18 16.95 91.87 60.74 28.39"/>
		<polygon class="face face-6" points="27.52 64.2 87.07 0 71.65 1.79 27.52 64.2"/>
	</svg>
</template>

<style scoped>
	.face {
		fill: var(--color-background);
		stroke: var(--color-text);
		stroke-width: 2pt;
		stroke-miterlimit: 10;
	}
	.face-6 {
		fill: var(--color-positive-die-4);
		/* fill: linear-gradient(to bottom, #8c92ac, #f5f5f5); */
		/* fill: #8c92ac; */
	}
	.face-5 {
		fill: var(--color-positive-die-6);
		/* fill: #f5f5f5; */
	}
	.face-4 {
		fill: var(--color-positive-die-12);
		/* fill: #003153; */
	}
	.face-3 {
		fill: var(--color-positive-die-8);
		/* fill: #ffffff; */
	}
	.face-2 {
		fill: var(--color-positive-die-10);
		/* fill: #a52a2a; */
	}
	.face-1 {
		fill: var(--color-positive-die-6);
		/* fill: #cc7722; */
	}
</style>
