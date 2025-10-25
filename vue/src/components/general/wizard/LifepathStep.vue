<script lang="ts" setup>
	import { ref, defineProps, defineEmits } from 'vue';
	import Option from './Option.vue';

	const props = defineProps<{
		currentStep: string;
		potentialSteps: string[];
	}>();

	const emits = defineEmits<{
		(event: 'nextStep', data: any): void;
	}>();

	const question = "What is your name?";
	const options = ["Alice", "Bob", "Charlie"];
	const answer = ref("");

	function answerQuestion(option: string) {
		answer.value = option;
	}
</script>

<template>
	<div>
		<h1>{{ props.currentStep }}</h1>
		<h2>{{ question }}</h2>
		<ol>
			<li v-for="option in options" :key="option" @click="answerQuestion(option)" :class="{ 'active': answer === option }">
				<Option>{{ option }}</Option>
			</li>
		</ol>
		<button v-for="step in props.potentialSteps" @click="emits('nextStep', step)">{{ step }}</button>
	</div>
</template>

<style scoped>
	.active {
		color: var(--color-highlight);
		border: 1px solid var(--color-highlight);
	}
</style>
