<script setup lang="ts">
	import { ref, type Ref, watch } from 'vue'
	import _ from 'lodash'
	import { v4 as uuidv4 } from 'uuid'

	import Die from '@/components/Die.vue'
	import type { Die as DieType } from '@/interfaces/Types'
	import { useDie, die_constants, placeholder_die } from '@/composables/Die'

	import { usePlayer } from '@/stores/Player'
	
	import { useDicepoolStore } from '@/stores/DicepoolStore'

	const dicepoolStore = useDicepoolStore()

	const props = defineProps<{
		die?: DieType,
		dice?: DieType[],
		resource?: boolean,
		custom?: boolean,
		show_effects?: boolean,
		preview?: boolean,
		dialogue?: boolean,
		negative?: boolean
	}>()

	const emit = defineEmits(['change-die', 'cancel'])

	const multiple = ref(props.dice && props.dice.length > 1 ? true : false)

	watch(() => props.die, (newDie) => {
		if(newDie) {
			return_rating.value = [newDie]
		}
	})

	watch(() => props.dice, (newDice) => {
		if(newDice) {
			return_rating.value = newDice
			newDice.forEach(d => {
				d.id = uuidv4()
			})
		}
	})

	watch(() => props.negative, (newNegative) => {
		if(newNegative) {
			sign.value = '-'
		}
	})

	const player = usePlayer()
	watch(player, (newPlayer) => {
		if(newPlayer.is_gm) {
			return_rating.value = []
		}
	})

	// const { die, change_rating, step_up, step_down } = useDie(props.die)

	const return_rating: Ref<DieType[]> = ref(props.die ? [props.die] : props.dice ? props.dice : [])
	const preview = ref(props.preview ?? true)

	function double() {
		return_rating.value.forEach((d) => {
			const { die, tag } = useDie(_.clone(d), undefined, undefined)
			tag()
			return_rating.value.push(die.value)
		})
	}

	function split() {
		return_rating.value.forEach((d) => {
			if(d.number_rating != die_constants[0].number_rating) {
				const index = return_rating.value.findIndex(x => x.id == d.id)
				return_rating.value.splice(index, 1)
				const { die: d1, tag: t1, change_type: c1 } = useDie(_.clone(d), undefined, undefined)
				const { die: d2, tag: t2, change_type: c2 } = useDie(_.clone(d), undefined, undefined)
				t1()
				c1(d.number_rating - 1)
				t2()
				c2(d.number_rating - 1)
				return_rating.value.push(d1.value)
				return_rating.value.push(d2.value)
			}
		})
	}

	function step_up() {
		return_rating.value.forEach((d) => {
			const { die, change_type } = useDie(d, undefined)
			change_type(die.value.number_rating + 1)
		})
	}

	function step_down() {
		return_rating.value.forEach((d) => {
			const { die, change_type } = useDie(d, undefined)
			change_type(die.value.number_rating - 1)
		})
	}

	function submit() {
		console.log("returning dice: " + JSON.stringify(return_rating.value))
		emit('change-die', return_rating.value)
	}

	function pick_die(d: number) {
		const { die, change_type } = useDie(undefined, undefined)
		change_type(d)
		die.value.traitId = props.die?.traitId ?? (die.value.traitId ?? (props.custom ? 'Traits/2' : undefined))
		die.value.entityId = props.die?.entityId ?? (die.value.entityId ?? (props.custom ? player.the_entity?.id : undefined))
		die.value.traitsetId = props.die?.traitsetId ?? (die.value.traitsetId ?? (props.custom ? 'Traitsets/3800280' : undefined))
		die.value.traitsettingId = props.die?.traitsettingId ?? (die.value.traitsettingId ?? (props.custom ? 'TraitSettings/1' : undefined))
		die.value.sfxId = props.die?.sfxId
		if(multiple.value) {
			return_rating.value.push(die.value)
		}
		else {
			return_rating.value = [die.value]
			submit()
		}
	}

	function remove_die(i: number) {
		return_rating.value.splice(i, 1)
	}

	const sign = ref(props.negative || (props.die?.number_rating ?? props.dice?.reduce((a, b) => a + b.number_rating, 0) ?? 0) < 0 ? '-' : '+')
</script>

<template>
	<div class="die-picker" :class="[
				props.custom ? 'vertical' : 'horizontal',
				sign == '-' ? 'negative' : 'positive'
			]">
		<div class="die-picker-wrapper" :class="{ 'small-buttons': player.small_buttons }">
			<input type="button" id="multiple-button" class="button multiple" :value="multiple ? '●●●' : '○●○'" @click.stop="multiple = !multiple" v-if="!props.custom" />
			<div class="dice">
				<span v-if="resource">add dice</span>
				<!-- <div class="negative-positive-indicator">±</div> -->
				<div class="negative-dice" v-if="!props.custom && sign == '-'">
					<span class="negative-positive-indicator button-mnml" @click="sign = '+'">{{ sign }}</span>
					<Die class="pickable-die" :die="{rating: 'd12', number_rating: -5}" @click.stop="pick_die(-5)" />
					<Die class="pickable-die" :die="{rating: 'd10', number_rating: -4}" @click.stop="pick_die(-4)" />
					<Die class="pickable-die" :die="{rating: 'd8', number_rating: -3}" @click.stop="pick_die(-3)" />
					<Die class="pickable-die" :die="{rating: 'd6', number_rating: -2}" @click.stop="pick_die(-2)" />
					<Die class="pickable-die" :die="{rating: 'd4', number_rating: -1}" @click.stop="pick_die(-1)" />
					<!-- <span class="negative-positive-indicator">-</span> -->
				</div>
				<div class="positive-dice" v-if="sign == '+'">
					<span class="negative-positive-indicator button-mnml" @click="sign = '-'" v-if="!props.custom">{{ sign }}</span>
					<!-- <span v-if="!props.custom" class="negative-positive-indicator">+</span> -->
					<Die class="pickable-die" :die="{rating: 'd4', number_rating: 1}" @click.stop="pick_die(1)" />
					<Die class="pickable-die" :die="{rating: 'd6', number_rating: 2}" @click.stop="pick_die(2)" />
					<Die class="pickable-die" :die="{rating: 'd8', number_rating: 3}" @click.stop="pick_die(3)" />
					<Die class="pickable-die" :die="{rating: 'd10', number_rating: 4}" @click.stop="pick_die(4)" />
					<Die class="pickable-die" :die="{rating: 'd12', number_rating: 5}" @click.stop="pick_die(5)" />
				</div>
				<span v-if="resource">remove dice</span>
				<div class="current-rating" v-if="!props.custom && props.preview && multiple">
					<Die v-for="(d, index) in return_rating" :key="d.id" :die="d" @click.stop="remove_die(index)" />
				</div>
				<div class="effect" v-if="!resource && props.die && show_effects">
					<input type="button" class="button-mnml" :value="player.small_buttons ? '▼' : '▼\nstep down'" @click.stop="step_down(); submit()" />
					<input type="button" class="button-mnml" :value="player.small_buttons ? '⇊' : '⇊\nsplit'" @click.stop="split(); submit()" />
					<input type="button" class="button-mnml" :value="player.small_buttons ? '⧉' : '⧉\ndouble'" @click.stop="double(); submit()" />
					<input type="button" class="button-mnml" :value="player.small_buttons ? '▲' : '▲\nstep up'" @click.stop="step_up(); submit()" />
					<input type="button" class="button-mnml cancel" :value="player.small_buttons ? 'x' : 'x\ncancel'" @click.stop="return_rating = [props.die]; submit()" />
				</div>
			</div>
			<div class="buttons" v-if="props.dice && props.dialogue">
				<input type="button" class="button-mnml submit" value="✓" @click.stop="submit()" v-if="!props.custom" />
				<input type="button" class="button-mnml cancel" value="x" @click.stop="emit('cancel')" v-if="!props.custom" />
			</div>
		</div>
	</div>
</template>

<style scoped>
	.die-picker {
		.die-picker-wrapper {
			display: flex;
			justify-content: space-between;
			/* position: relative;
			#multiple-button {
				position: absolute;
				left: 0;
				top: 0;
			} */
			.effect {
				width: 100%;
				min-height: 3em;
				display: flex;
				justify-content: center;
				background-color: var(--color-border);
				gap: 1px;
				border-top: 1px solid var(--color-border);
				border-bottom: none;
				overflow: hidden;
				.button-mnml {
					background-color: var(--color-background);
					width: 20%;
				}
			}
			.dice {
				flex-grow: 1;
				display: flex;
				flex-direction: column;
				align-items: center;
				.negative-positive-indicator {
					font-size: 2em;
					font-weight: bold;
					padding: 0 0.4em;
				}
				.pickable-die {
					cursor: pointer;
					margin: 0 0.4em;
				}
			}
			.buttons {
				display: flex;
				flex-direction: column;
				flex-grow: 1;
				border-left: 1px solid var(--color-border);
				.button-mnml {
					width: 100%;
					flex-grow: 1;
					font-size: 1.2em;
					&.submit {
						border-bottom: 1px solid var(--color-border);
						background-color: var(--color-highlight);
						color: var(--color-highlight-text);
					}
				}
			}
		}
	}
	.die-picker.vertical {
		height: 100%;
		.die-picker-wrapper {
			height: 100%;
			.dice {
				height: 100%;
				display: flex;
				flex-direction: column;
				justify-content: space-evenly;
			}
		}
	}
	.die-picker.horizontal {
		/* padding: 0 1em; */
		&.positive {
			border: 1px solid var(--color-positive-die-12);
			box-shadow: inset 0px 0px 10px var(--color-positive-die-12);
		}
		&.negative {
			border: 1px solid var(--color-hitch);
			box-shadow: inset 0px 0px 10px var(--color-hitch);
		}
		border-radius: 10px;
		overflow: hidden;
		.dice {
			overflow: hidden;
			.negative-dice, .positive-dice {
				display: flex;
				justify-content: center;
				align-items: center;
			}
		}
	}
</style>
