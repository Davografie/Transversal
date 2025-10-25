<script lang="ts" setup>
	import Lifepath1 from './wizard/LifepathStep.vue';
	import { reactive } from 'vue';
	const step_tree = reactive({
		current_step: 'lifepath_1',
		steps: {
			lifepath_1: {
				component: Lifepath1,
				next_steps: ["lifepath_2"],
			},
			lifepath_2: {
				component: Lifepath1,
				next_steps: ["lifepath_1", "lifepath_3"],
			},
			lifepath_3: {
				component: Lifepath1,
				next_steps: ["lifepath_1", "lifepath_2"],
			}
		},
	});
	function goToNextStep(to: string) {
		step_tree.current_step = to;
	}
</script>

<template>
	<div class="wizard-wrapper">
		<Lifepath1
			:key="step_tree.current_step"
			:current-step="step_tree.current_step"
			:potential-steps="step_tree.steps[step_tree.current_step].next_steps"
			@next-step="goToNextStep" />
	</div>
</template>

<style scoped>
.wizard-wrapper {
	border: 1px solid #ccc;
	padding: 1rem;
	border-radius: 0.5rem;
	background-color: var(--color-background-mute);
	h1 {
		text-decoration: underline;
	}
}
</style>
