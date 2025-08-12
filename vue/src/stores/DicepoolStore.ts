/*
	dicepool store
	state:
		a collection of dicepools
		one for every active player
		including the current user
*/
import { ref, type Ref, computed, watch, onMounted } from 'vue'
import { defineStore } from 'pinia'
import { v4 as uuidv4 } from 'uuid'

import type { Die, Resolution, Dicepool } from '@/interfaces/Types'

export enum phases {
	ADDING = "add dice to pool",
	ROLLING = "rolling...",
	RESULT = "pick result dice",
	EFFECT = "pick effect dice",
	RESOLVE = "resolving dicepools...",
	SWADE_RESULT = "result"
}

export const useDicepoolStore = defineStore('dicepool', () => {

	const phase: Ref<phases> = ref(phases.ADDING)
	function set_phase(p: phases) {
		phase.value = p
	}

	const dicepools: Ref<Array<Dicepool>> = ref([])

	// complications is a set of traits of the complication traitset offered by this user to the opposing dicepools
	const complications: Ref<Array<Die>> = ref([])
	// suggested_complications is a set of traits of the complications traitset given by opposing players to this user
	const suggested_complications: Ref<Array<Die>> = ref([])

	const resolutions: Ref<Array<Resolution>> = ref([])
	const resolutions_rev: Ref<string> = ref("")
	const pull_resolutions: Ref<boolean> = ref(true)

	const dice: Ref<Array<Die>> = ref([])
	const dicepool_limit: Ref<number> = ref(5)

	const result_limit: Ref<number> = ref(2)
	const result = computed(() => {
		let result = 0
		for(const d of dice.value) {
			if(d.result && d.isResultDie) {
				result += d.result
			}
		}
		return result
	})

	const effect_limit: Ref<number> = ref(1)
	const effect: Ref<string[]> = computed(() => {
		let result = []
		for(const d of dice.value) {
			if(d.isEffectDie) {
				result.push(d.rating)
			}
		}
		return result
	})
	
	function add_die(d: Die, force?: boolean) {
		if(phase.value == phases.ADDING || force) {
			d.pool = true
			if(!d.id) d.id = uuidv4()
			dice.value.push(d)
		}
	}

	function add_dice(ds: Die[], force?: boolean) {
		if(phase.value == phases.ADDING || force) {
			for(let d of ds) {
				if(dice.value.length < dicepool_limit.value) {
					d.pool = true
					if(!d.id) d.id = uuidv4()
					dice.value.push(d)
				}
			}
		}
	}

	function remove_die(d: Die) {
		const index = dice.value.indexOf(d)
		dice.value.splice(index, 1)
	}

	function roll() {
		phase.value = phases.ROLLING
		dice.value.forEach(die => {
			die.result = Math.ceil(Math.random() * Number(die.rating.slice(1)))
		})
		phase.value = phases.RESULT
	}

	function populate_resolutions() {
		// retrieve resolutions of other players' dicepools
		// should eventually be resolved by SocketIO polling
		// resolutions.value = []
	}

	// const max_result = computed(() => {
	// 	return resolutions.value.reduce((max, dp) => (dp.result > max.result ? dp : max), resolutions.value[0]).result
	// })

	function empty() {
		dice.value = []
		resolutions.value = []
		phase.value = phases.ADDING
	}

	return {
		phase,
		phases,
		set_phase,
		// max_result,
		dicepools,
		complications,
		suggested_complications,
		resolutions,
		resolutions_rev,
		pull_resolutions,
		dice,
		dicepool_limit,
		result_limit,
		result,
		effect_limit,
		effect,
		add_die,
		add_dice,
		remove_die,
		roll,
		empty
	}
},
{
	// https://github.com/prazdevs/pinia-plugin-persistedstate
	persist: {
		debug: true,
		paths: [
			'dice',
			'complications',
			'phase',
			'dicepool_limit',
			'result_limit',
			'effect_limit',
			'resolutions_rev'
		],
	},
},)