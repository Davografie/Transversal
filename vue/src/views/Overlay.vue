<script setup lang="ts">
import NewDicepoolView from '@/views/NewDicepoolView.vue'
import { overlay_types, type Entity } from '@/interfaces/Types'
const props = defineProps<{
	overlay_type: overlay_types,
	entity?: Entity
}>()
const emits = defineEmits(['close_overlay'])
</script>

<template>
	<div id="overlay">
		<div id="image-overlay" v-if="props.overlay_type == overlay_types.IMG && props.entity?.image" @click="emits('close_overlay')">
			<span id="image-name" class="header">{{ props.entity.name }}</span>
			<img id="image-img" :src="'/assets/uploads/' + props.entity.image.path + 'original' + props.entity.image.ext" @click.stop />
		</div>
		<NewDicepoolView v-else-if="props.overlay_type == overlay_types.DICEPOOL" />
	</div>
</template>

<style scoped>
#overlay {
	position: fixed;
	top: 0;
	left: 0;
	width: 100vw;
	height: 100vh;
	#image-overlay {
		width: 100%;
		height: 100%;
		cursor: pointer;
		#image-name {
			position: absolute;
			bottom: 0;
			left: 0;
			width: 100vw;
			height: 100vh;
			text-align: center;
			font-size: 32vw;
			color: var(--color-text);
			display: flex;
			flex-direction: column;
			justify-content: end;
			align-items: center;
			line-height: .7em;
			letter-spacing: -.12em;
		}
		#image-img {
			position: absolute;
			top: 50%;
			left: 50%;
			transform: translate(-50%, -50%);
			max-width: 100%;
			max-height: 100%;
			padding: 2em;
			background-color: var(--color-text);
			cursor: default;
		}
	}
}
</style>

<style>
.landscape #overlay {
	z-index: 12;
}
.dark #overlay {
	background-color: var(--color-background-mute);
}
.light #overlay {
	background-color: var(--color-background);
}
</style>
