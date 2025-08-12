/*
	Die logic
*/
import { ref } from "vue"
import type { Ref } from "vue"
import { v4 as uuidv4 } from 'uuid'
import _ from "lodash"
import type { Die } from "@/interfaces/Types"

export const placeholder_die: Die = {
	number_rating: 0,
	rating: 'd100'
}
export const placeholder_d4: Die = {
	number_rating: 1,
	rating: 'd4'
}
export const placeholder_d6: Die = {
	number_rating: 2,
	rating: 'd6'
}
export const placeholder_d8: Die = {
	number_rating: 3,
	rating: 'd8'
}
export const placeholder_d10: Die = {
	number_rating: 4,
	rating: 'd10'
}
export const placeholder_d12: Die = {
	number_rating: 5,
	rating: 'd12'
}
export const die_constants = [
	{
		rating: "d12",
		number_rating: -5,
		sides: 12,
		active: "⬟",
		inactive: "⬠",
	},
	{
		rating: "d10",
		number_rating: -4,
		sides: 10,
		active: "⬢",
		inactive: "⬡",
	},
	{
		rating: "d8",
		number_rating: -3,
		sides: 8,
		active: "◆",
		inactive: "◇",
	},
	{
		rating: "d6",
		number_rating: -2,
		sides: 6,
		active: "■",
		inactive: "□",
	},
	{
		rating: "d4",
		number_rating: -1,
		sides: 4,
		active: "▲",
		inactive: "△",
	},
	{
		rating: "d4",
		number_rating: 1,
		sides: 4,
		active: "▲",
		inactive: "△",
	},
	{
		rating: "d6",
		number_rating: 2,
		sides: 6,
		active: "■",
		inactive: "□",
	},
	{
		rating: "d8",
		number_rating: 3,
		sides: 8,
		active: "◆",
		inactive: "◇",
	},
	{
		rating: "d10",
		number_rating: 4,
		sides: 10,
		active: "⬢",
		inactive: "⬡",
	},
	{
		rating: "d12",
		number_rating: 5,
		sides: 12,
		active: "⬟",
		inactive: "⬠",
	}
]
interface DieShapes {
	[key: string]: string;
	default_active: string;
	default_inactive: string;
	d4_active: string;
	d4_inactive: string;
	d6_active: string;
	d6_inactive: string;
	d8_active: string;
	d8_inactive: string;
	d10_active: string;
	d10_inactive: string;
	d12_active: string;
	d12_inactive: string;
  }
export const die_shapes: DieShapes = {
	default_active: "●",
	default_inactive: "○",
	d4_active: "▲",
	d4_inactive: "△",
	d6_active: "■",
	d6_inactive: "□",
	d8_active: "◆",
	d8_inactive: "◇",
	d10_active: "⬢",
	d10_inactive: "⬡",
	d12_active: "⬟",
	d12_inactive: "⬠"
}


export function useDie(init?: Die, die_type?: string, number_rating?: number) {
	const die: Ref<Die> = ref(init
		?? _.clone(die_constants.find(d => d.number_rating == number_rating))
		?? _.clone(die_constants.find(d => d.rating ?? '' == die_type))
		?? placeholder_die)

	// onMounted(() => {
	// 	if(init) {
	// 		die.value = init
	// 	}
	// 	else if(die_type) {
	// 		die.value = {rating: die_type, number_rating: die_constants.find(d => d.rating == die_type).number_rating}
	// 	}
	// 	if(!die.value.id) tag()
	// })

	if(!die.value.id) tag()

	function tag() {
		die.value.id = uuidv4()
	}

	function roll(explosive?: boolean) {
		const die_values = die_constants.find(d => d.rating == die.value.rating)
		const sides = die.value.sides ?? die_values?.sides ?? 0
		if(explosive) die.value.result = explosive_roll(sides)
		else die.value.result = Math.ceil(Math.random() * sides)
		if(die.value.result == 1) die.value.isHitch = true
	}

	function explosive_roll(sides: number = 4) {
		let result = 0
		const roll = Math.ceil(Math.random() * sides)
		result += roll
		if (roll == sides) {
			result += explosive_roll(sides)
		}
		return result
	}

	function change_type(dieType: number) {
		die.value.number_rating = dieType
		die.value.sides = die_constants.find(d => d.number_rating == dieType)?.sides
		die.value.rating = die_constants.find(d => d.number_rating == dieType)?.rating ?? 'd100'
	}

	function change_rating(rating: string) {
		die.value.rating = rating
	}

	function step_up(steps: number = 1) {
		const die_index = die_constants.findIndex(d => d.rating == die.value.rating)
		if(die_index + steps < die_constants.length) {
			die.value.rating = die_constants[
				die_constants.findIndex(d => d.rating == die.value.rating) + steps
			].rating
		}
	}

	function step_down() {
		if(die.value.rating != die_constants[0].rating) {
			die.value.rating = die_constants[die_constants.findIndex(d => d.rating == die.value.rating) - 1].rating
		}
	}

	return {
		die,
		change_rating,
		change_type,
		tag,
		roll,
		step_up,
		step_down
	}
}
