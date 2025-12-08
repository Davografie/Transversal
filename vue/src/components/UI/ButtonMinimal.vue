<script setup lang="ts">
	import IconAddArchetype from '@/components/icons/IconAddArchetype.vue';
	import { ButtonTypes, useButtonTypes } from '@/composables/Button';
	const props = defineProps<{
		function: ButtonTypes
	}>()
	const { label } = useButtonTypes(props.function as ButtonTypes)
</script>

<template>
	<div class="minimal-button">
		<IconAddArchetype v-if="props.function == 'add_archetype'" />
		<div class="label">
			{{ label }}
		</div>
	</div>
</template>

<style scoped>
</style>

<style>
	.dark {
		.minimal-button {
			background-color: var(--color-background-mute);
			text-align: center;
			display: flex;
			flex-direction: column;
			justify-content: center;
			.label {
			}
		}
	}
</style>
