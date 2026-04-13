<script setup lang="ts">
import { usePlayerStore } from '@/stores/PlayerStore';

const playerStore = usePlayerStore();
</script>

<template>
	<div id="image-overlay" v-if="playerStore.image_entity?.image" @click="playerStore.image_entity = undefined">
		<span id="image-name" class="header">{{ playerStore.image_entity.name }}</span>
		<img id="image-img" :src="'/assets/uploads/' + playerStore.image_entity.image.path + 'original' + playerStore.image_entity.image.ext" />
	</div>
</template>

<style scoped>
#image-overlay {
	position: fixed;
	top: 0;
	left: 0;
	width: 100vw;
	height: 100vh;
	/* background-size: contain;
	background-repeat: no-repeat;
	background-position: center; */
	z-index: 11; /* above all */
	cursor: pointer;
	#image-name {
		position: absolute;
		bottom: 0;
		left: 0;
		/* left: 50%; */
		/* transform: translateX(-50%); */
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
		/* line-height: 50vh; */
		/* overflow-x: auto;
		overflow-y: hidden; */
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
	}
}
</style>

<style>
.dark {
	#image-overlay {
		backdrop-filter: blur(5px);
	}
}
.light {
	#image-overlay {
		background-color: var(--color-background);
	}
}
.triptych {
	#image-overlay {
		#image-name {
			/* transform: translateX(-50%) translateY(-2em); */
			padding-bottom: .8em;
		}
		#image-img {
			transform: translateX(-50%) translateY(-70%);
		}
	}
}
</style>
