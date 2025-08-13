<script setup lang="ts">
	import { computed } from 'vue'
	import type { Die } from '@/interfaces/Types'
	import { die_constants } from '@/composables/Die'
	import { useDicepoolStore, phases } from '@/stores/DicepoolStore'
	const dicepool = useDicepoolStore()
	
	const props = defineProps<{
		die: Die,
		amount?: number,
		is_choice?: boolean,
		in_pool?: boolean
	}>()
	
	const render_result = computed(() => {
		return (
			props.in_pool // only show results in the dicepool
			&& props.die.result // and only when there is a result to show
			&& (
				props.die.isHitch
				|| props.die.isResultDie
				|| dicepool.phase == phases.RESULT && !props.die.isResolved
				|| (
					(dicepool.phase == phases.RESOLVE || props.die.isResolved)
					&& (props.die.isResultDie || props.die.isHitch)
				)
			)
		) ?? false
	})

	const is_disabled = computed(() => {
		if(dicepool.phase == phases.RESULT) {
			return props.is_choice && (props.die.isHitch || props.die.isResultDie || props.die.isEffectDie)
		}
		else if(dicepool.phase == phases.EFFECT) {
			return props.is_choice && (props.die.isHitch == true || props.die.isResultDie == true || props.die.isEffectDie == true)
		}
		else {
			return false
		}
	})
</script>

<template>
	<div class="die" :class="[
			props.die.rating,
			props.die.number_rating > 0 ? 'positive' : 'negative',
			dicepool.phase === phases.RESULT ? 'RESULT'
			: dicepool.phase === phases.EFFECT ? 'EFFECT'
			: '',
			{ 'disabled': is_disabled && !props.die.isHitch },
			{ 'show-result': render_result },
			{ 'result': props.die.isResultDie },
			{ 'effect': props.die.isEffectDie },
			{ 'hitch': props.die.isHitch }]"
			@contextmenu="(e) => e.preventDefault()">
		<svg class="die" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 46.74 50.47" v-if="props.die.rating == 'd4'">
			<polygon class="shape" points="1.71 44.58 23.38 1.75 44.53 44.58 1.71 44.58"/>
			<text class="label" text-anchor="middle" dominant-baseline="middle" transform="translate(23.38 30)">
				<tspan x="0" y="0" @contextmenu="(e) => e.preventDefault()">
					{{ props.amount ? props.amount : '' }}{{ render_result ? props.die.isHitch ? '!' : props.die.result : props.die.rating }}
				</tspan>
			</text>
		</svg>
		<svg class="die" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 46.74 50.47" v-if="props.die.rating == 'd6'">
			<rect class="shape" x="2.37" y="2.69" width="42" height="42"/>
			<text class="label" text-anchor="middle" dominant-baseline="middle" transform="translate(23.38 25.23)">
				<tspan x="0" y="0" @contextmenu="(e) => e.preventDefault()">
					{{ props.amount ? props.amount : '' }}{{ render_result ? props.die.isHitch ? '!' : props.die.result : props.die.rating }}
				</tspan>
			</text>
		</svg>
		<svg class="die" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 46.74 50.47" v-if="props.die.rating == 'd8'">
			<polygon class="shape" points="45.66 35.22 45.66 12.16 23.79 .64 1.93 12.16 1.93 35.22 23.79 46.75 45.66 35.22"/>
			<text class="label" text-anchor="middle" dominant-baseline="middle" transform="translate(23.38 25.23)">
				<tspan x="0" y="0" @contextmenu="(e) => e.preventDefault()">
					{{ props.amount ? props.amount : '' }}{{ render_result ? props.die.isHitch ? '!' : props.die.result : props.die.rating }}
				</tspan>
			</text>
		</svg>
		<svg class="die" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 46.74 50.47" v-if="props.die.rating == 'd10'">
			<path class="shape" d="m45.66,17.85L23.83,1.46,2.6,16.78l-.67,9.55c.14.07,21.01,19.58,21.01,19.58l22.65-18.74.08-9.32Z"/>
			<text class="label" text-anchor="middle" dominant-baseline="middle" transform="translate(23.38 25.23)">
				<tspan x="0" y="0" @contextmenu="(e) => e.preventDefault()">
					{{ props.amount ? props.amount : '' }}{{ render_result ? props.die.isHitch ? '!' : props.die.result : props.die.rating }}
				</tspan>
			</text>
		</svg>
		<svg class="die" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 46.74 50.47" v-if="props.die.rating == 'd12'">
			<polygon class="shape" points="36.89 43.01 22.76 47.1 8.86 42.3 .5 30.44 .88 16.05 9.85 4.62 23.99 .52 37.88 5.33 46.24 17.19 45.86 31.58 36.89 43.01"/>
			<text class="label" text-anchor="middle" dominant-baseline="middle" transform="translate(23.38 25.23)">
				<tspan x="0" y="0" @contextmenu="(e) => e.preventDefault()">
					{{ props.amount ? props.amount : '' }}{{ render_result ? props.die.isHitch ? '!' : props.die.result : props.die.rating }}
				</tspan>
			</text>
		</svg>
	</div>
</template>

<style scoped>
	.die.d4.positive svg {
		.shape {
			fill: var(--color-positive-die-4);
			stroke: var(--color-positive-die-4-text);
		}
		.label {
			fill: var(--color-positive-die-4-text);
			stroke: var(--color-positive-die-4-text-outline);
			paint-order: stroke fill;
			stroke-width: 2px;
			stroke-linejoin: round;
			stroke-linecap: round;
		}
	}
	.die.d4.negative svg {
		.shape {
			fill: var(--color-negative-die-4);
			stroke: var(--color-negative-die-4-text);
		}
		.label {
			fill: var(--color-negative-die-4-text);
			stroke: var(--color-negative-die-4-text-outline);
			paint-order: stroke fill;
			stroke-width: 2px;
			stroke-linejoin: round;
			stroke-linecap: round;
		}
	}
	.die.d6.positive svg {
		.shape {
			fill: var(--color-positive-die-6);
			stroke: var(--color-positive-die-6-text);
		}
		.label {
			fill: var(--color-positive-die-6-text);
			stroke: var(--color-positive-die-6-text-outline);
			paint-order: stroke fill;
			stroke-width: 2px;
			stroke-linejoin: round;
			stroke-linecap: round;
		}
	}
	.die.d6.negative svg {
		.shape {
			fill: var(--color-negative-die-6);
			stroke: var(--color-negative-die-6-text);
		}
		.label {
			fill: var(--color-negative-die-6-text);
			stroke: var(--color-negative-die-6-text-outline);
			paint-order: stroke fill;
			stroke-width: 2px;
			stroke-linejoin: round;
			stroke-linecap: round;
		}
	}
	.die.d8.positive svg {
		.shape {
			fill: var(--color-positive-die-8);
			stroke: var(--color-positive-die-8-text);
		}
		.label {
			fill: var(--color-positive-die-8-text);
			stroke: var(--color-positive-die-8-text-outline);
			paint-order: stroke fill;
			stroke-width: 2px;
			stroke-linejoin: round;
			stroke-linecap: round;
		}
	}
	.die.d8.negative svg {
		.shape {
			fill: var(--color-negative-die-8);
			stroke: var(--color-negative-die-8-text);
		}
		.label {
			fill: var(--color-negative-die-8-text);
			stroke: var(--color-negative-die-8-text-outline);
			paint-order: stroke fill;
			stroke-width: 2px;
			stroke-linejoin: round;
			stroke-linecap: round;
		}
	}
	.die.d10.positive svg {
		.shape {
			fill: var(--color-positive-die-10);
			stroke: var(--color-positive-die-10-text);
		}
		.label {
			fill: var(--color-positive-die-10-text);
			stroke: var(--color-positive-die-10-text-outline);
			paint-order: stroke fill;
			stroke-width: 2px;
			stroke-linejoin: round;
			stroke-linecap: round;
		}
	}
	.die.d10.negative svg {
		.shape {
			fill: var(--color-negative-die-10);
			stroke: var(--color-negative-die-10-text);
		}
		.label {
			fill: var(--color-negative-die-10-text);
			stroke: var(--color-negative-die-10-text-outline);
			paint-order: stroke fill;
			stroke-width: 2px;
			stroke-linejoin: round;
			stroke-linecap: round;
		}
	}
	.die.d12.positive svg {
		.shape {
			fill: var(--color-positive-die-12);
			stroke: var(--color-positive-die-12-text);
		}
		.label {
			fill: var(--color-positive-die-12-text);
			stroke: var(--color-positive-die-12-text-outline);
			paint-order: stroke fill;
			stroke-width: 2px;
			stroke-linejoin: round;
			stroke-linecap: round;
		}
	}
	.die.d12.negative svg {
		.shape {
			fill: var(--color-negative-die-12);
			stroke: var(--color-negative-die-12-text);
		}
		.label {
			fill: var(--color-negative-die-12-text);
			stroke: var(--color-negative-die-12-text-outline);
			paint-order: stroke fill;
			stroke-width: 2px;
			stroke-linejoin: round;
			stroke-linecap: round;
		}
	}
	.die {
		display: inline-block;
		height: 2.8em;
		width: 2.8em;
		position: relative;
		text-align: center;
		line-height: 0;
		overflow: visible;
		text-shadow: none;
		z-index: 1;
		&.positive {
			font-family: var(--dice-font-positive);
		}
		&.negative {
			font-family: var(--dice-font-negative);
		}
	}
	.die.result.RESULT, .die.effect.EFFECT {
		border-radius: 50%;
		background-image: radial-gradient(var(--color-highlight) 0%, var(--color-background) 100%);
		box-shadow: 0 0 5px var(--color-highlight);
	}
	.label {
		top: 18px;
		left: 1px;
		text-align: center;
		font-size: 1.4em;
	}
	.show-result .label {
		font-size: 2.4em;
	}
	.effect .label {
		color: var(--color-highlight-text);
		font-weight: bold;
	}
	.disabled {
		.label {
			fill: var(--color-disabled-text) !important;
			stroke: var(--color-disabled-text-outline) !important;
		}
		.shape {
			fill: var(--color-disabled) !important;
			stroke: var(--color-disabled-text) !important;
		}
	}
	.hitch .label {
		color: var(--color-hitch-text);
	}
</style>

