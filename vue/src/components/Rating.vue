<script setup lang="ts">
	import { ref, computed } from 'vue'
	import _ from 'lodash'
	import Die from '@/components/Die.vue'

	import type { Die as DieType } from '@/interfaces/Types'

	const props = defineProps<{
		rating: DieType[]
		ratingType?: string
	}>()

	const emit = defineEmits(['deplete-resource', 'deplete-challenge'])

	const distinct = computed(() => {
		return _.uniq(props.rating.map((d) => d.number_rating))
	})

	const componentHeight = computed(() => {
		return props.ratingType == 'resource' ? 'auto' : '32px'
	})

	const show_dice_number = ref(4)
</script>

<template>
	<div class="rating-wrapper" :class="props.ratingType" v-if="props.ratingType != 'empty'">

		<Die
			v-if="props.ratingType != 'resource' && props.ratingType != 'challenge'"
			v-for="d in props.rating" :key="d.id"
			:die="d" />

		<Die
			v-if="props.ratingType == 'challenge' && (props.rating.length <= show_dice_number || distinct.length > 1)"
			v-for="d in props.rating" :key="d.id"
			:die="d"
			@click.stop="emit('deplete-challenge', d)" />

		<Die
			v-if="props.ratingType == 'challenge' && props.rating.length > show_dice_number && distinct.length == 1"
			v-for="d in props.rating.slice(0, 1)" :key="d.id"
			:die="d"
			:amount="props.rating.length"
			@click.stop="emit('deplete-challenge', d)" />

		<div class="distinct-resource" v-if="props.ratingType == 'resource'" v-for="dc in distinct">
			<Die
				v-for="d in props.rating.filter((r) => r.number_rating == dc).slice(0, 1)" :key="d.id"
				:die="d"
				:amount="props.rating.filter((r) => r.number_rating == dc).length"
				@click.stop="emit('deplete-resource', d)" />
		</div>

	</div>
</template>

<style scoped>
	.rating-wrapper {
		max-height: 100%;
		display: flex;
		&.resource {
			display: flex;
			gap: 1em;
			.distinct-resource {
				line-height: 0;
			}
		}
		&.challenge {
			display: flex;
			flex-wrap: wrap;
			justify-content: end;
			position: relative;
			z-index: 1;
		}
	}
</style>

<style>
</style>
