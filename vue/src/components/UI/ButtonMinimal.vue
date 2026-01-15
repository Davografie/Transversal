<script setup lang="ts">
	// import IconAddArchetype from '@/components/icons/IconAddArchetype.vue';
	// import IconSwitch from '@/components/icons/IconSwitch.vue';
	
	// import { computed } from 'vue'
	import { usePlayer } from '@/stores/Player';

	import { ButtonTypes, useButtonTypes } from '@/composables/Button';

	const props = defineProps<{
		function: ButtonTypes
	}>()

	const player = usePlayer()

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
		<div class="label" v-if="!player.small_buttons">
			{{ label }}
		</div>
	</div>
</template>

<style scoped>
	.minimal-button {
		cursor: pointer;
		text-align: center;
		display: flex;
		flex-direction: column;
		justify-content: center;
	}
</style>

<style>
	.dark {
		.minimal-button {
			/* background-color: var(--color-background-mute); */
			.icon {
				min-width: 2em;
				min-height: 2em;
			}
			.label {
			}
			&.active {
				background-color: var(--color-background-mute);
			}
		}
	}
</style>
