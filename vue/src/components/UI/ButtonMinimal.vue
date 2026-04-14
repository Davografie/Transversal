<script setup lang="ts">
	// import IconAddArchetype from '@/components/icons/IconAddArchetype.vue';
	// import IconSwitch from '@/components/icons/IconSwitch.vue';
	
	// import { computed } from 'vue'
	import { usePlayerStore } from '@/stores/PlayerStore';

	import { ButtonTypes, useButtonTypes } from '@/composables/Button';

	const props = defineProps<{
		function: ButtonTypes,
		label?: string
		hide_label?: boolean
	}>()

	const player = usePlayerStore()

	// const the_component = computed(() => {
	// 	switch(props.function) {
	// 		case ButtonTypes.ADD_ARCHETYPE:
	// 			return IconAddArchetype
	// 		case ButtonTypes.SWITCH:
	// 			return IconSwitch
	// 	}
	// })
	const { label, the_component } = useButtonTypes(props.function as ButtonTypes)
</script>

<template>
	<div class="minimal-button">
		<!-- <IconAddArchetype v-if="props.function == 'add_archetype'" /> -->
		<component class="icon" :is="the_component" />
		<div class="label" v-if="!player.small_buttons && props.hide_label == false">
			{{ props.label ?? label }}
		</div>
	</div>
</template>

<style scoped>
	.minimal-button {
		cursor: pointer;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: end;
		flex-grow: 1;
		/* height: 100%; */
		.icon {
			width: 2em;
			height: 2em;
			flex-grow: 5;
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: end;
		}
		.label {
			flex-grow: 1;
			text-align: center;
			line-height: 0.9em;
			/* height: 1.4em; */
		}
	}
</style>

<style>
	.dark {
		.minimal-button {
			/* background-color: var(--color-background-mute); */
			/* backdrop-filter: blur(5px); */
			text-shadow: var(--text-shadow);
			.icon {
				width: 1em;
				height: 1em;
			}
			.label {
			}
			&.active {
				text-shadow: var(--text-glow);
				/* background-color: var(--color-background-mute); */
			}
		}
	}
	.light .minimal-button {
		&.active {
			background-color: var(--color-highlight-mute);
		}
	}
</style>
