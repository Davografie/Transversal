<script setup lang="ts">
	import { ref, computed } from 'vue'
	import _ from 'lodash'
	import Die from '@/components/Die.vue'

	import type { Die as DieType } from '@/interfaces/Types'

	const props = defineProps<{
		rating: DieType[]
		ratingType?: string
		scaling?: number
	}>()

	const emit = defineEmits([
		'deplete-resource',
		'deplete-challenge',
		'increase-challenge'
	])

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
		
		<div class="scaling" v-if="props.scaling && props.scaling != 0">
			{{ props.scaling < 0 ? '-' : '+' }}{{ props.scaling }}
		</div>

		<div class="dice">
			<Die
				v-if="props.ratingType != 'resource' && props.ratingType != 'challenge'"
				v-for="d in props.rating" :key="d.id"
				:die="d" />

			<Die
				v-if="props.ratingType == 'challenge' && (props.rating.length <= show_dice_number || distinct.length > 1)"
				v-for="d in props.rating" :key="d.id"
				:die="d"
				@click.stop="emit('deplete-challenge', d)"
				@click.right.stop="emit('increase-challenge', d)" />

			<Die
				v-if="props.ratingType == 'challenge' && props.rating.length > show_dice_number && distinct.length == 1"
				v-for="d in props.rating.slice(0, 1)" :key="d.id"
				:die="d"
				:amount="props.rating.length"
				@click.stop="emit('deplete-challenge', d)"
				@click.right.stop="emit('increase-challenge', d)" />

			<div class="distinct-resource" v-if="props.ratingType == 'resource'" v-for="dc in distinct">
				<Die
					v-for="d in props.rating.filter((r) => r.number_rating == dc).slice(0, 1)" :key="d.id"
					:die="d"
					:amount="props.rating.filter((r) => r.number_rating == dc).length"
					@click.stop="emit('deplete-resource', d)" />
			</div>
		</div>

	</div>
</template>

<style scoped>
	.rating-wrapper {
		max-height: 100%;
		display: flex;
		align-items: center;
		gap: .4em;
		&.resource .dice {
			/* display: flex; */
			gap: 1em;
			.distinct-resource {
				line-height: 0;
			}
		}
		&.challenge .dice {
			/* display: flex; */
			flex-wrap: wrap;
			justify-content: end;
			position: relative;
			z-index: 1;
		}
		.scaling {
			font-size: 1.6em;
			transform: translateY(-.1em);
			color: var(--color-result-light);
			letter-spacing: -.15em;
			/* font-family: "Bevan", serif; */
			font-weight: bold;
			font-style: normal;
		}
	}
</style>

<style>
</style>
