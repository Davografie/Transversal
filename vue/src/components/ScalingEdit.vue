<script setup lang="ts">
	import { ref, computed, watch, onMounted } from 'vue'
	import { useScroll, useElementBounding } from '@vueuse/core';
	// const props = defineProps<{
	// 	scaling: number
	// 	min?: number
	// 	max?: number
	// }>()
	// const emit = defineEmits([
	// 	'change-scaling'
	// ])
	const props = defineProps({
		scaling: {
			type: Number,
			required: true
		},
		min: {
			type: Number,
			default: -3
		},
		max: {
			type: Number,
			default: 6
		}
	})
	const emit = defineEmits<{
		change_scaling: [scaling: number]
	}>()
	const new_scaling = ref(props.scaling)
	// const number_array: number[] = [-3, -2, -1, 0, 1, 2, 3, 4, 5, 6].reverse()
	const number_array: number[] = Array.from({ length: props.max - props.min + 1 }, (_, i) => props.max - i)
	const number_wrapper = ref<HTMLDivElement>()
	const { y, isScrolling,  } = useScroll(number_wrapper)
	const { height } = useElementBounding(number_wrapper)
	const scrolling = ref(false)

	const selected = computed(() => {
		return Math.max(...number_array) - Math.round(y.value / height.value)
	})

	function scroll_to_selected() {
		scrolling.value = true
		number_wrapper.value!.scrollTo({
			top: height.value * (Math.max(...number_array) - new_scaling.value),
			behavior: 'smooth'
		})
	}

	// watch(() => props.scaling, () => {
	// 	scroll_to_selected()
	// })

	onMounted(() => {
		scroll_to_selected()
	})

	watch(selected, (newSelected) => {
		if(!isScrolling && !scrolling.value) {
			emit('change_scaling', newSelected)
		}
	})

	watch(isScrolling, (newIsScrolling) => {
		if(isScrolling && !scrolling.value) {
			scrolling.value = true
		}
		if(!newIsScrolling) {
			scrolling.value = false
		}
		if(!newIsScrolling && props.scaling != selected.value) {
			new_scaling.value = selected.value
			emit('change_scaling', selected.value)
		}
	})

	// watch(new_scaling, () => {
	// 	// scroll to selected scaling
	// 	scroll_to_selected()
	// 	emit('change_scaling', new_scaling.value)
	// })

	function change_scaling(n: number) {
		if(number_array.includes(n + new_scaling.value)) {
			new_scaling.value += n
		}
		scroll_to_selected()
	}
</script>

<template>
	<div class="scaling-edit">
		<input value="▲" type="button" class="button-mnml" @click="change_scaling(1)" />
		<div class="number-wrapper" ref="number_wrapper">
			<span class="scale-number" v-for="n of number_array" :key="n" @click="emit('change_scaling', n)" :class="{ 'selected': n == new_scaling }">
				{{ n }}
			</span>
		</div>
		<input value="▼" type="button" class="button-mnml" @click="change_scaling(-1)" />
	</div>
</template>

<style scoped>
.scaling-edit {
	display: flex;
	flex-direction: column;
	/* justify-content: center; */
	align-items: center;
	.number-wrapper {
		font-family: "Bevan", serif;
		height: 2em;
		width: 2em;
		display: flex;
		flex-direction: column;
		scroll-snap-type: y mandatory;
		scroll-behavior: smooth;
		overflow: hidden auto;
		.scale-number {
			height: inherit;
			width: inherit;
			scroll-snap-align: center;
			text-align: center;
			font-size: 1.2em;
		}
	}
}
</style>
