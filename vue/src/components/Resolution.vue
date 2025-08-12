<script setup lang="ts">
	import { ref, watch } from 'vue'

	import { sum } from 'lodash'

	import ResolvedDie from '@/components/ResolvedDie.vue'
	import Die from '@/components/Die.vue'

	import { useDie } from '@/composables/Die'

	import type { Resolution, Die as DieType } from '@/interfaces/Types'

	const props = defineProps<{
		resolution: Resolution,
		winner: boolean,
		heroic?: number,
		verbose?: boolean
	}>()

	// const verbose_dice = ref(props.verbose ?? false)
	const effect = ref<DieType[]>(props.resolution.dice.filter((d) => d.isEffectDie))

	watch(() => props.resolution.dice, (newDice) => {
		effect.value = []
		newDice.filter((d) => d.isEffectDie).forEach((d) => {
			const { die, step_up } = useDie(d, undefined)
			step_up(props.heroic ?? 0)
			effect.value.push(die.value)
		})
	})
</script>

<template>
	<div class="resolution" :class="props.winner ? 'winner' : 'not-winner'">
		
		<div class="result" v-if="!props.verbose && props.resolution.dice.some((d) => d.isResolved)">
			<div class="result-segment score">
				<span>result</span>
				<span class="header">{{ sum(props.resolution.dice.filter((d) => d.isResultDie).map((d) => d.result)) }}</span>
				<!-- <Die v-for="d in props.resolution.dice.filter((d) => d.isResultDie)" :key="d.id" :die="d" in_pool /> -->
			</div>
			<div class="result-segment effect-dice">
				<span>effect</span>
				<Die v-for="d in effect" :key="d.id" :die="d" in_pool />
			</div>
			<div class="result-segment hitches" v-if="props.resolution.dice.some((d) => d.isHitch)">
				<span>hitches</span>
				<Die v-for="d in props.resolution.dice.filter((d) => d.isHitch)" :key="d.id" :die="d" in_pool />
			</div>
		</div>

		<div class="verbose-dice" v-if="props.verbose && props.resolution.dice.some((d) => d.isResolved)">
			<div class="result-dice" v-if="props.resolution.dice.some((d) => d.isResultDie)">
				<div class="resolution-die-type header">
					<div>
						Result
					</div>
					<div>
						{{ sum(props.resolution.dice.filter((d) => d.isResultDie).map((d) => d.result)) }}
					</div>
				</div>
				<ResolvedDie v-for="d in props.resolution.dice.filter((d) => d.isResultDie)" :key="d.id" :die="d"
					:entity="!props.resolution.dice.map((d) => d.entityId).every((val, i, arr) => val === arr[0])" />
			</div>
			<div class="effect-dice" v-if="effect.length > 0">
				<div class="resolution-die-type header">Effect</div>
				<ResolvedDie v-for="d in effect" :key="d.id" :die="d"
					:entity="!props.resolution.dice.map((d) => d.entityId).every((val, i, arr) => val === arr[0])" />
			</div>
			<div class="hitches" v-if="props.resolution.dice.some((d) => d.isHitch)">
				<div class="resolution-die-type header">Hitches</div>
				<ResolvedDie v-for="d in props.resolution.dice.filter((d) => d.isHitch)" :key="d.id" :die="d"
					:entity="!props.resolution.dice.map((d) => d.entityId).every((val, i, arr) => val === arr[0])" />
			</div>
		</div>
	</div>
</template>

<style scoped>
	.resolution {
		background-color: var(--color-background-mute);
		padding: .4em .6em;
		.player {
			font-size: xx-small;
		}
		.result {
			display: flex;
			gap: .4em;
			.result-segment {
				display: flex;
				flex-direction: column;
				align-items: center;
				&.score .header {
					font-size: 1.6em;
				}
			}
		}
		.verbose-dice {
			.resolution-die-type {
				padding: 0 .4em;
				display: flex;
				justify-content: space-evenly;
			}
		}
	}
</style>

<style>
	.dark {
		.resolution {
			border-radius: 20px;
			overflow: hidden;
			.verbose-dice {
				.resolution-die-type {
					background-color: var(--color-background-mute);
					color: var(--color-text);
					text-shadow: none;
				}
				.result-dice {
					box-shadow: inset 0 0 100px var(--color-background);
				}
				.effect-dice {
					box-shadow: inset 0 0 100px var(--color-highlight-mute);
				}
				.hitches {
					box-shadow: inset 0 0 100px var(--color-hitch);
				}
			}
		}
		.resolution.winner {
			background-image: linear-gradient(90deg, var(--color-highlight) -50%, var(--color-background) 20%, var(--color-background) 80%, var(--color-highlight) 150%);
			border-left: 1px solid var(--color-highlight);
			border-right: 1px solid var(--color-highlight);
		}
		.resolution.not-winner {
			background-image: linear-gradient(90deg, var(--color-hitch) -50%, var(--color-background) 20%, var(--color-background) 80%, var(--color-hitch) 150%);
			border-left: 1px solid var(--color-hitch);
			border-right: 1px solid var(--color-hitch);
		}
	}
	.light {
		.resolution.winner {
			background-color: var(--color-highlight-mute);
		}
	}
</style>
