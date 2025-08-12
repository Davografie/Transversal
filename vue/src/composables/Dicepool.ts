/*
	dicepool composable logic
*/
import { ref, computed, watch, inject, onMounted } from "vue"
import { useFetch } from "@vueuse/core"

import { useDie, placeholder_die } from "@/composables/Die"
import type { Dicepool, Die, Resolution } from "@/interfaces/Types"

import { useSession } from "@/composables/Session"
import { useDicepoolStore } from "@/stores/DicepoolStore"
import { usePlayer } from "@/stores/Player"
import _ from "lodash"
import { useTrait } from "./Trait"


export const placeholder_dicepool: Dicepool = {
	player: "",
	dice: [placeholder_die]
}

export function useDicepool() {
	const dicepool = useDicepoolStore()
	const player = usePlayer()
	const { get_session, get_dicepool_limit } = useSession()

	const resolutions_count = computed(() => dicepool.resolutions.length)

	const interval = ref(10000)

	const API_URL = inject<string>('API_URL')

	const inAddingPhase = computed(() => dicepool.phase == dicepool.phases.ADDING)
	const inResultPhase = computed(() => dicepool.phase == dicepool.phases.RESULT)
	const inEffectPhase = computed(() => dicepool.phase == dicepool.phases.EFFECT)
	const inResolvePhase = computed(() => dicepool.phase == dicepool.phases.RESOLVE)
	const inSwadeResultPhase = computed(() => dicepool.phase == dicepool.phases.SWADE_RESULT)

	/**
	 * Changes the result limit by `+n`
	 * @param n the change in result limit
	 */
	function change_result_limit(n: number) {
		dicepool.result_limit += n
	}

	function change_effect_limit(n: number) {
		dicepool.effect_limit += n
	}

	function add_die(d: Die) {
		if(!d.id) {
			const { die } = useDie(d)
			d = die.value
		}
		d.pool = true
		dicepool.dice.push(d)
		push_dicepool()
	}

	function add_dice(dice: Die[]) {
		dice.forEach(d => {
			d.pool = true
			dicepool.dice.push(_.clone(d))
		})
		push_dicepool()
	}

	function add_complication(die: Die) {
		dicepool.complications.push(die)
		push_complications()
	}

	function remove_complication_by_traitsetting(traitsettingId: string) {
		if(check_trait(traitsettingId)) dicepool.complications = dicepool.complications.filter((c) => c.traitsettingId != traitsettingId)
		if(check_subtrait(traitsettingId)) dicepool.complications = dicepool.complications.filter((c) => c.subTraitsettingId != traitsettingId)
		push_complications()
	}

	const { trait_setting_id, trait, retrieve_trait, mutate_trait_setting } = useTrait(undefined, undefined, undefined, undefined)

	function remove_die(d: Die) {
		console.log("dicepool: removing die: ", d)
		const index = dicepool.dice.map((d) => d.id).indexOf(d.id)
		if(dicepool.dice.map((d) => d.id).includes(d.id)) {

			// if it's a complication, make sure to edit the suggested complication's meta data
			// this meta-data is used to check whether or not the suggested complication should be shown
			if(dicepool.suggested_complications.map((sc) => sc.id).includes(d.id)) {
				dicepool.suggested_complications.filter((sc) => sc.id == d.id)
					.forEach((sc) => sc.pool = false)
			}

			// if it's a resource die, then the resource should be given back to that trait
			trait_setting_id.value = d.traitsettingId

			retrieve_trait()

			watch(trait, (newTrait) => {
				if(newTrait.ratingType == 'resource' && trait_setting_id.value) {
					const new_rating = [...newTrait.rating ?? [], d]
					mutate_trait_setting({rating: new_rating.map((r) => r.number_rating)})
					change_result_limit(-1)
				}
				trait_setting_id.value = undefined
			})



			dicepool.dice.splice(index, 1)
			push_dicepool()
		}
	}
	
	function toggle_result(d: Die) {
		const index = dicepool.dice.indexOf(d)
		if(result_size.value < dicepool.result_limit && !d.isResultDie && !d.isEffectDie && !d.isHitch) {
			dicepool.dice[index].isResultDie = true
		}
		else if(d.isResultDie) {
			dicepool.dice[index].isResultDie = false
		}
	}

	function toggle_effect(d: Die) {
		const index = dicepool.dice.indexOf(d)
		if(effect_size.value < dicepool.effect_limit && !d.isResultDie && !d.isEffectDie && !d.isHitch) {
			dicepool.dice[index].isEffectDie = true
		}
		else if(d.isEffectDie) {
			dicepool.dice[index].isEffectDie = false
		}
	}

	function roll() {
		// swade roll
		if(dicepool.dice.length <= 2) {
			if(player.the_entity?.entityType == 'character' && dicepool.dice.length == 1) {
				// add wild die
				const { die, tag, change_type } = useDie(_.clone(dicepool.dice[0]), undefined, 2)
				tag()
				change_type(2)
				add_die(die.value)
			}
			dicepool.dice.forEach(d => {
				const { roll: rollSwade } = useDie(d, undefined)
				rollSwade(true)
				d.raises = Math.floor(((d.result ?? 4) - 4) / 4)
				d.isResultDie = true
				d.isResolved = true
			})
			dicepool.dice.sort((d1, d2) => d2.result - d1.result)
			dicepool.phase = dicepool.phases.SWADE_RESULT
		}

		// cortex roll
		else if(dicepool.dice.length > 1) {
			dicepool.phase = dicepool.phases.ROLLING
			dicepool.dice.forEach(d => {
				const { die, roll } = useDie(d, undefined)
				roll()
				d.result = die.value.result
			})
			dicepool.phase = dicepool.phases.RESULT
		}
	}

	/**
	 * Check if a trait is in the dicepool
	 * @param traitSettingId - the id of the traitsetting
	 * @returns true if the trait is in the dicepool, false otherwise
	 */
	function check_trait(traitSettingId: string) {
		return dicepool.dice.some((d) => d.traitsettingId == traitSettingId)
			|| dicepool.complications.some((c) => c.traitsettingId == traitSettingId)
	}

	/**
	 * Check if a trait is in the dicepool as a subtrait
	 * @param traitSettingId - the id of the traitsetting
	 * @returns true if the trait is in the dicepool, false otherwise
	 */
	function check_subtrait(traitSettingId: string) {
		return dicepool.dice.some((d) => d.subTraitsettingId == traitSettingId)
			|| dicepool.complications.some((c) => c.subTraitsettingId == traitSettingId)
	}

	function check_die(id: string) {
		return dicepool.dice.some((d) => d.id == id)
	}
	
	//	removes all dice of a given traitsetting
	function remove_traitsetting_dice(traitsettingId: string) {
		if(check_trait(traitsettingId)) dicepool.dice = dicepool.dice.filter(d => (d.traitsettingId ?? 'custom') != traitsettingId)
		if(check_subtrait(traitsettingId)) dicepool.dice = dicepool.dice.filter(d => (d.subTraitsettingId ?? 'custom') != traitsettingId)
		push_dicepool()
	}

	//	returns the dice of traits in the dicepool of a given traitset
	function traitset_dice(traitset: string) {
		return [
			...dicepool.dice.filter(d => d.traitsetId == traitset),
			...dicepool.complications.filter(c => c.traitsetId == traitset)
		]
	}

	function trait_dice(traitsetting_id: string) {
		return [
			...dicepool.dice.filter(d => d.traitsettingId == traitsetting_id),
			...dicepool.complications.filter(c => c.traitsettingId == traitsetting_id)
		]
	}

	function subtrait_dice(traitsetting_id: string) {
		return [
			...dicepool.dice.filter(d => d.subTraitsettingId == traitsetting_id),
			...dicepool.complications.filter(c => c.subTraitsettingId == traitsetting_id)
		]
	}

	const dicepool_size = computed(() => dicepool.dice ? dicepool.dice.length : 0)
	const dicepool_limit = computed(() => dicepool.dicepool_limit)

	function change_dicepool_limit(n: number) {
		dicepool.dicepool_limit += n
	}

	const result_size = computed(() => dicepool.dice.filter(d => d.isResultDie).length)
	const result_limit = computed(() => dicepool.result_limit)
	const result = computed(() => dicepool.dice.filter(d => d.isResultDie).reduce((sum, d) => sum + d.result, 0))
	const effect_size = computed(() => dicepool.dice.filter(d => d.isEffectDie).length)
	const effect_limit = computed(() => dicepool.effect_limit)
	const effect = computed(() => dicepool.dice.filter(d => d.isEffectDie))
	const hitches_size = computed(() => dicepool.dice.filter(d => d.result == 1).length)

	function next() {
		if(dicepool.phase == dicepool.phases.ADDING) dicepool.phase = dicepool.phases.ROLLING
		else if(dicepool.phase == dicepool.phases.ROLLING) dicepool.phase = dicepool.phases.RESULT
		else if(dicepool.phase == dicepool.phases.RESULT) {
			dicepool.phase = dicepool.phases.EFFECT
			if(dicepool.dice.filter(d => !d.isResultDie && !d.isHitch).length == 0) {
				add_die({
					traitsettingId: "TraitSettings/1",
					// entity is most common entity (not being a complication) in the dicepool
					entityId: dicepool.dice.filter(d => d.traitsettingId != 'TraitSettings/1')
						.map(d => d.entityId)
						.reduce(
							(a, b) => (dicepool.dice.filter(d => d.entityId == a).length >= dicepool.dice.filter(d => d.entityId == b).length) ? a : b
						),
					rating: "d4",
					number_rating: 1
				})
			}
		}
		else if(dicepool.phase == dicepool.phases.EFFECT) {
			dicepool.dice.forEach(d => {
				d.isResolved = true
			})
			dicepool.phase = dicepool.phases.RESOLVE
			new Set(dicepool.dice.filter(d => d.traitsetId != 'Traitsets/1').map(d => d.entityId)).forEach(e => {
				new Set(dicepool.dice.filter(d => d.traitsetId == 'Traitsets/1').map(d => d.traitsettingId)).forEach(od => {
					e && od ? teach_character(od, e) : null
				})
			})
		}
	}

	function set_result_phase() {
		dicepool.phase = dicepool.phases.RESULT
	}

	function set_effect_phase() {
		dicepool.phase = dicepool.phases.EFFECT
	}

	function empty_dicepool() {
		console.log("emptying dicepool")
		dicepool.dice = []
		dicepool.complications = []
		dicepool.phase = dicepool.phases.ADDING
		dicepool.result_limit = 2
		dicepool.effect_limit = 1
	}
	
	//	this function pushes the current player's dicepool to the server
	function push_dicepool() {
		const resolution: Resolution = {
			player: {
				uuid: player.uuid || "",
				player_name: player.player_name || "",
				is_gm: player.is_gm,
				phase: dicepool.phase.toString()
			},
			dice: dicepool.dice
		}
		const url = API_URL + "set-dicepool/" + player.uuid
		const { data } = useFetch(url).post(resolution).json()
		watch(data, (newData) => {
			console.log("resolution data set update: ", newData)
			if(newData && newData.resolutions) {
				dicepool.resolutions = newData.resolutions
			}
			else {
				console.log("set dicepool fetch error: ", newData)
			}
		})
	}

	function push_complications() {
		const url = API_URL + "add-complications/" + player.uuid
		const { data } = useFetch(url).post({complications: dicepool.complications}).json()
		
		watch(data, (newData) => {
			console.log("complication push data update: ", newData)
			if(newData && newData.complication_pool) {
				dicepool.complications = newData.complication_pool.map((cp: any) => cp.complications)
			}
			else {
				console.log("add complication fetch error: ", newData)
			}
		})
	}

	async function teach_character(_trait_setting_id: string, _character_id: string) {
		trait_setting_id.value = _trait_setting_id
		retrieve_trait()
		while(!trait.value) {
			await new Promise(r => setTimeout(r, 10));
		}
		mutate_trait_setting({teachTo: _character_id})
	}
	
	//	this function pulls the active dicepools from the server
	function pull_dicepools() {
		get_session()
		const url = API_URL + "get-resolutions/" + dicepool.resolutions_rev
		const { data } = useFetch(url).get().json()
		watch(data, (newData) => {
			if(newData.resolutions_rev != dicepool.resolutions_rev) {
				console.log("dicepool polling: dicepool changed")
				
				// update resolutions
				if(newData.resolutions && newData.resolutions.length > 0) {
					console.log("resolution data get update: ", newData.resolutions)
					dicepool.resolutions = newData.resolutions.filter((r: Resolution) => !r.winner)

					if(newData.resolutions.some((r: Resolution) => r.winner)) {
						let winner: Resolution = newData.resolutions.splice(
							newData.resolutions.findIndex((r: Resolution) => r.winner), 1)[0]
						winner.heroic = newData.heroic
						dicepool.resolutions.push(winner)
					}

					// make sure encountered traits are henceforth known to characters
					// only after resolution
					console.error("teaching")
					console.log("resolutions: ", newData.resolutions)
					dicepool.resolutions.filter((r: Resolution) => r.player.phase == dicepool.phases.RESOLVE.toString() && r.player.uuid != player.uuid)
							.forEach((r: Resolution) => {
						console.log("resolution: ", r)
						new Set(r.dice.map((d: Die) => d.traitsettingId)).forEach((trait_setting_id) => {
							console.log("trait_id: ", trait_setting_id)
							dicepool.dice.map((d: Die) => d.entityId)
								.forEach((entity_id) => {
									console.log("character: ", entity_id)
									trait_setting_id && trait_setting_id != 'traitSettings/1' && entity_id ? teach_character(trait_setting_id, entity_id) : null
							})
						})
					})
				}
				else if(newData.resolutions && newData.resolutions.length == 0) {
					dicepool.resolutions = []
				}

				let complication_dice: Die[] = []
				if(newData.complication_pool) {
					console.log("complication data get update: complications detected, flattening complication pool:", newData.complication_pool)
					// complications are grouped by player
					// here the dice are extracted and put into a flat array
					complication_dice = newData.complication_pool
						.filter((cp: any) => cp.player != player.uuid)
						.map((cp: any) => cp.complications).flat()
				}

				if(complication_dice.length > 0) {
					// here the array of complication dice are added to the dicepool store
					// as suggestions, the player can then choose which to add to their dicepool
					console.log("complication data get update: adding complication suggestions: ", complication_dice)
					complication_dice.forEach((c: Die) => {
						if(!dicepool.suggested_complications.map((sc: Die) => sc.id).includes(c.id)) {
							console.log("adding complication suggestion: ", c,
								" to suggested_complications: ", dicepool.suggested_complications)
							// dicepool.suggested_complications.push(_.cloneDeep(c))
							dicepool.suggested_complications = [...dicepool.suggested_complications, _.clone(c)]
							console.log("new suggested_complications: ", dicepool.suggested_complications)
						}
					})
				}
				else {
					console.log("complication data get update: no complications detected, emptying suggested_complications.")
					dicepool.suggested_complications = []
				}

				// finally the suggested complications in the dicepool that have been removed
				// from the complication pool online, should also be removed from the suggestions
				console.log("complication data get update: removing complication suggestions not in complication pool.")
				dicepool.suggested_complications = dicepool.suggested_complications.filter((sc: Die) => {
					return complication_dice.map((c: Die) => c.id).includes(sc.id)
				})

				dicepool.resolutions_rev = newData.resolutions_rev
			}
		})
	}

	function pull_clock() {
		pull_dicepools()
		if(!stop_clock.value) {
			setTimeout(pull_clock, interval.value)
		}
		else {
			console.log("stopping dicepool pull polling")
		}
	}

	const stop_clock = ref(false)

	function clear_dicepool() {
		console.log("clearing dicepool")
		dicepool.dice = []
		dicepool.complications = []
		push_complications()

		get_dicepool_limit()
		// watch(() => session.dicepool_limit.value, (newLimit) => {
		// 	dicepool.dicepool_limit = newLimit
		// })

		dicepool.result_limit = 2
		dicepool.effect_limit = 1

		dicepool.phase = dicepool.phases.ADDING
		push_dicepool()

		dicepool.$persist()
	}

	watch(() => player.beat_id, (newBeatId, oldBeatId) => {
		if(oldBeatId && newBeatId && newBeatId != oldBeatId) {
			console.log("beat id changed from ", oldBeatId, " to ", newBeatId , ", clearing dicepool")
			clear_dicepool()
		}
	})

	//	this function clears all dicepools on the server, only for GM
	function clear_dicepools() {
		console.log("clearing all dicepools")
		const url = API_URL + "reset-dicepool"
		const { data } = useFetch(url).post().json()
		watch(data, (newData) => {
			console.log("resolution data update: ", newData)
			if(newData && newData.success) {
				dicepool.empty()
				console.log("reset dicepool successful")
			}
			else {
				console.log("reset dicepool fetch error: ", newData)
			}
		})
	}

	return {
		resolutions_count,
		inAddingPhase,
		inResultPhase,
		inEffectPhase,
		inResolvePhase,
		inSwadeResultPhase,
		set_result_phase,
		set_effect_phase,
		add_die,
		add_dice,
		add_complication,
		remove_complication_by_traitsetting,
		remove_die,
		remove_traitsetting_dice,
		roll,
		check_trait,
		check_subtrait,
		check_die,
		traitset_dice,
		trait_dice,
		dicepool_size,
		dicepool_limit,
		change_dicepool_limit,
		result_size,
		result_limit,
		change_result_limit,
		toggle_result,
		result,
		effect_size,
		effect_limit,
		change_effect_limit,
		hitches_size,
		toggle_effect,
		effect,
		next,
		push_dicepool,
		pull_dicepools,
		pull_clock,
		stop_clock,
		pullInterval: interval,
		clear_dicepool,
		clear_dicepools
	}
}
