<script setup lang="ts">
import { useDicepoolStore } from '@/stores/DicepoolStore';
import PoolPlayer from '@/components/PoolPlayer.vue';
const emits = defineEmits(['close_overlay'])
const { dicepools } = useDicepoolStore()
</script>

<template>
	<div id="new-dicepool" @click.stop>
		<h1>DICEPOOLS</h1>
		<div id="close-dicepool-button" class="button-mnml" @click.stop="emits('close_overlay')">
			✖
		</div>
		<div id="players">
			<PoolPlayer class="player" v-for="dicepool in dicepools" :key="dicepool.player.key" :dicepool="dicepool" />
		</div>
	</div>
</template>

<style scoped>
#close-dicepool-button {
	position: absolute;
	top: 0;
	right: 10px;
	z-index: 1;
	font-size: 2em;
}
</style>

<style>
.dark #new-dicepool {
	margin: 2em;
	width: calc(100% - 4em);
	height: calc(100% - 4em);
	border-radius: 2em;
	padding: 2em;
	background-color: var(--color-background-mute);
	backdrop-filter: blur(20px);
	box-shadow: 0 0 20px var(--color-background);
	border: 1px solid var(--color-border);
	h1 {
		color: var(--color-background-soft);
		text-shadow: 0 0 3px var(--color-text);
	}
}
.landscape #new-dicepool {
	#players {
		display: flex;
		gap: 1em;
		justify-content: center;
		flex-direction: row;
		flex-wrap: wrap;
	}
}
</style>
