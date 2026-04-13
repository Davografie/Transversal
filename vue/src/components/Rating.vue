<script setup lang="ts">
	import { ref, computed } from 'vue'
	import _ from 'lodash'
	import Die from '@/components/Die.vue'

	import type { Die as DieType } from '@/interfaces/Types'

	const props = defineProps<{
		rating: DieType[]
		ratingType?: string
		pool_scaling?: number
		result_scaling?: number
		effect_scaling?: number
		die_size?: string
	}>()

	const emit = defineEmits([
		'deplete-resource',
		'deplete-challenge',
		'increase-challenge'
	])

	const distinct = computed(() => {
		return _.uniq(_.sortBy(props.rating.map((d) => d.number_rating)))
	})

	const componentHeight = computed(() => {
		return props.ratingType == 'resource' ? 'auto' : '32px'
	})

	const show_dice_number = ref(4)
</script>

<template>
	<div class="rating-wrapper" :class="props.ratingType" v-if="props.ratingType != 'empty'">
		
		<div class="pool-scaling scaling" v-if="props.pool_scaling && props.pool_scaling != 0">
			{{ props.pool_scaling < 0 ? '-' : '+' }}{{ props.pool_scaling }}
		</div>

		<div class="result-scaling scaling" v-if="props.result_scaling && props.result_scaling != 0">
			{{ props.result_scaling < 0 ? '-' : '+' }}{{ props.result_scaling }}
		</div>

		<div class="effect-scaling scaling" v-if="props.effect_scaling && props.effect_scaling != 0">
			{{ props.effect_scaling < 0 ? '-' : '+' }}{{ props.effect_scaling }}
		</div>

		<div class="dice">
			<Die
				v-if="props.ratingType != 'resource' && props.ratingType != 'challenge'"
				v-for="d in props.rating" :key="d.id"
				:die="d"
				:size="props.die_size" />

			<Die
				v-if="props.ratingType == 'challenge' && (props.rating.length <= show_dice_number || distinct.length > 1)"
				v-for="d in props.rating" :key="d.id"
				:die="d"
				@click.stop="emit('deplete-challenge', d)"
				@click.right.stop="emit('increase-challenge', d)"
				:size="props.die_size" />

			<Die
				v-if="props.ratingType == 'challenge' && props.rating.length > show_dice_number && distinct.length == 1"
				v-for="d in props.rating.slice(0, 1)" :key="d.id"
				:die="d"
				:amount="props.rating.length"
				@click.stop="emit('deplete-challenge', d)"
				@click.right.stop="emit('increase-challenge', d)"
				:size="props.die_size" />

			<div class="distinct-resource" v-if="props.ratingType == 'resource'" v-for="dc in distinct">
				<Die
					v-for="d in props.rating.filter((r) => r.number_rating == dc).slice(0, 1)" :key="d.id"
					:die="d"
					:amount="props.rating.filter((r) => r.number_rating == dc).length"
					@click.stop="emit('deplete-resource', d)"
					:size="props.die_size" />
			</div>
		</div>

	</div>
</template>

<style scoped>
.rating-wrapper {
	max-height: 100%;
	display: flex;
	align-items: center;
	gap: 1em;
	&.resource .dice {
		display: flex;
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
		letter-spacing: -.15em;
		/* font-family: "Bevan", serif; */
		font-weight: bold;
		font-style: normal;
		/* &.result-scaling {
			color: var(--color-result-light);
		} */
		&.effect-scaling {
			color: var(--color-effect);
		}
	}
}
</style>

<style>
.dark {
	.rating-wrapper {
		.scaling.result-scaling {
			color: var(--color-result-light);
		}
	}
}
.light {
	.rating-wrapper {
		.scaling.result-scaling {
			color: var(--color-result);
		}
	}
}
</style>
