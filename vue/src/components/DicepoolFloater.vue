<script setup lang="ts">
import { ref } from 'vue';
import { useDraggable } from '@vueuse/core';
import { useTemplateRef } from 'vue';
const emits = defineEmits(['engage'])
const dicepool_floater = useTemplateRef('dicepool_floater');
const { style } = useDraggable(dicepool_floater, {
	initialValue: { x: 650, y: 20 },
	onMove: () => { clickable.value = false },
	onEnd: () => { setTimeout(() => clickable.value = true, 100) },
	preventDefault: true
});
const clickable = ref(true)
function clickity() {
	if (clickable.value) {
		emits('engage')
	}
}
</script>

<template>
	<div id="dicepool-floater" :class="{ 'dragging': !clickable }" ref="dicepool_floater" :style="style" @click="clickity">
		🎲
	</div>
</template>

<style scoped>
#dicepool-floater {
	position: absolute;
	font-size: 4em;
	z-index: 10;
	cursor: pointer;
	&.dragging {
		cursor: move;
	}
}
</style>

<style>
.dark #dicepool-floater {
	text-shadow: var(--text-glow),
		0 0 40px var(--color-background),
		0 0 60px var(--color-background),
		0 0 80px var(--color-background),
		0 0 100px var(--color-background);
}
</style>
