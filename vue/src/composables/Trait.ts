/*
	Trait logic
*/
import _ from "lodash"

import { ref, watch, inject } from "vue"
import type { Ref } from "vue"

import type { ApolloClient, FetchPolicy } from '@apollo/client/core'
import { useQuery, useMutation, provideApolloClient } from "@vue/apollo-composable"
import gql from 'graphql-tag'

import { useRating } from "@/composables/Rating"
import { useTrait as useRecursiveTrait } from "@/composables/Trait"
import type { Trait, TraitSetting, TraitSettingInput, TraitInput, Die as DieType } from "@/interfaces/Types"

export const placeholder_trait: Trait = {
	id: "placeholder",
	name: "loading",
	rating: []
}

	// enable/disable trait edit mode
export enum view_modes {
	Small = 'small',
	Neutral = 'neutral',
	Editing = 'editing',
	Viewing = 'viewing'
}

export const rating_types: string[] = ['empty', 'static', 'resource', 'challenge']


export function useTrait(init?: Trait, _trait_id?: string, _trait_setting_id?: string, _entity_id?: string) {
	const apolloClient = inject<ApolloClient<Cache>>('apolloClient')
	
	const trait: Ref<Trait> = ref(init ?? placeholder_trait)
	const default_settings: Ref<TraitSetting|undefined> = ref()

	const trait_id = ref(_trait_id)
	const trait_setting_id = ref(_trait_setting_id)
	const entity_id = ref(_entity_id)
	const instances: Ref<TraitSetting[]> = ref([])

	async function retrieve_trait(caching: FetchPolicy = 'cache-first') {
		const query_get_trait = gql`query TraitByID($traitId: ID) {
			traits(traitId: $traitId) {
				id
				name
				explanation
				requiredTraits {
					id
					name
				}
				locationRestricted
				possibleSubTraits {
					id
					name
					traitset {
						id
					}
				}
				sfxs {
					id
				}
				inheritable
			}
		}`
		const query_get_setting_trait = gql`query TraitBySetting($traitSettingId: ID, $traitId: ID) {
			traits(traitSettingId: $traitSettingId, traitId: $traitId) {
				id
				name
				explanation
				traitsetId
				traitset {
					id
					entityTypes
				}
				traitSettingId
				traitSetting {
					statement
					notes
					rating
					ratingType
					permanence
					poolScaling
					resultScaling
					effectScaling
					locationsEnabled
					locationsDisabled
					knownTo {
						id
					}
					hidden
					fromEntity {
						id
						name
					}
					toEntity {
						id
						name
					}
					inherited
					inheritable
				}
				requiredTraits {
					id
					name
				}
				ratingType
				rating
				statement
				notes
				sfxs {
					id
				}
				subTraits {
					id
					traitSettingId
					rating
					ratingType
					traitSetting {
						poolScaling
						resultScaling
						effectScaling
					}
				}
				possibleSubTraits {
					id
					name
					traitset {
						entityTypes
					}
					traitSettingId
				}
			}
		}`

		// used for character cards
		const query_get_entity_trait = gql`query CharacterCardTraits($traitId: ID, $entityId: ID) {
			traits(traitId: $traitId, entityId: $entityId) {
				id
				name
				requiredTraits {
					id
					name
				}
				ratingType
				rating
				statement
				traitSetting {
					poolScaling
					resultScaling
					effectScaling
				}
				sfxs {
					id
				}
				subTraits {
					id
					traitSettingId
					rating
					traitSetting {
						poolScaling
						resultScaling
						effectScaling
					}
				}
			}
		}`
		if(apolloClient) {
			let query = query_get_trait
			let args: object = { traitId: trait_id.value }
			if(trait_setting_id.value) {
				query = query_get_setting_trait
				args = {
					traitSettingId: trait_setting_id.value,
					traitId: trait_id.value
				}
			}
			else if(trait_id.value && entity_id.value) {
				query = query_get_entity_trait
				args = { traitId: trait_id.value, entityId: entity_id.value }
			}

			const result = await apolloClient.query({
				query: query,
				variables: args,
				fetchPolicy: caching
			}).catch((error) => {
				console.error("error retrieving trait(" + trait_id.value + "): ", error)
			})

			if(result && result.data && result.data.traits && result.data.traits.length > 0) {
				// console.log("retrieved trait: ", result.data.traits[0])
				let newTrait = result.data.traits[0]
				if(newTrait.rating) {
					const new_rating = convert_rating_to_dice(
						newTrait.rating, // this is actually a number, as it is retrieved from GraphQL
						newTrait.ratingType,
						newTrait.id,
						newTrait.traitSettingId,
						newTrait.traitsetId,
						entity_id.value,
						newTrait.traitSetting.scaling
					)
					newTrait = { ...newTrait, rating: new_rating }
				}
				if(result.data.traits[0].subTraits && result.data.traits[0].subTraits.length > 0) {
					const new_subTraits = []
					for(const subTrait of result.data.traits[0].subTraits) {
						let new_subTrait = { ...subTrait }
						if(new_subTrait.rating) {
							const new_rating = convert_rating_to_dice(
								new_subTrait.rating, // this is actually a number, as it is retrieved from GraphQL
								new_subTrait.ratingType,
								new_subTrait.id,
								new_subTrait.traitSettingId,
								new_subTrait.traitsetId,
								entity_id.value,
								new_subTrait.traitSetting.scaling
							)
							new_subTrait = { ...new_subTrait, rating: new_rating }
						}
						new_subTraits.push(new_subTrait)
					}
					newTrait = { ...newTrait, subTraits: new_subTraits }
				}

				trait.value = newTrait
			}


			// const { result } = provideApolloClient(apolloClient)(
			// 	() => useQuery<{traits: Trait[]}>(
			// 		query,
			// 		args,
			// 		{ fetchPolicy: 'cache-and-network' }
			// 	)
			// )
			// watch(result, (newResult) => {
			// 	if(newResult && newResult.traits?.length > 0) {
			// 		let newTrait = newResult.traits[0]
			// 		if(newResult.traits[0].rating) {
			// 			const new_rating = convert_rating_to_dice(
			// 				newResult.traits[0].rating, // this is actually a number, as it is retrieved from GraphQL
			// 				newResult.traits[0].ratingType,
			// 				newResult.traits[0].id,
			// 				newResult.traits[0].traitSettingId,
			// 				newResult.traits[0].traitsetId,
			// 				entity_id.value
			// 			)
			// 			newTrait = {
			// 				...newTrait,
			// 				rating: new_rating
			// 			}
			// 		}
			// 		if(newResult.traits[0].subTraits) {
			// 			let newSubTraits = <Trait[]>[]
			// 			for(let i = 0; i < newResult.traits[0].subTraits.length; i++) {
			// 				let newSubTrait = newResult.traits[0].subTraits[i]
			// 				if(newResult.traits[0].subTraits[i].rating) {
			// 					const new_rating = convert_rating_to_dice(
			// 						newResult.traits[0].subTraits[i].rating, // this is actually a number, as it is retrieved from GraphQL
			// 						newResult.traits[0].subTraits[i].ratingType,
			// 						newResult.traits[0].subTraits[i].id,
			// 						newResult.traits[0].subTraits[i].traitSettingId,
			// 						newResult.traits[0].subTraits[i].traitsetId,
			// 						entity_id.value
			// 					)
			// 					newSubTrait = {
			// 						...newSubTrait,
			// 						rating: new_rating
			// 					}
			// 					newSubTraits.push(newSubTrait)
			// 				}
			// 			}
			// 			newTrait = {
			// 				...newTrait,
			// 				subTraits: newSubTraits
			// 			}
			// 		}
			// 		trait.value = newTrait
			// 	}
			// })
		}
	}

	const { convert_rating_to_dice } = useRating()

	function retrieve_trait_setting(caching: FetchPolicy = 'cache-first') {
		const query = gql`query TraitSettingByID($traitSettingId: ID) {
			traits(traitSettingId: $traitSettingId) {
				possibleSubTraits {
					id
					name
					traitset {
						id
						entityTypes
					}
				}
				traitSetting {
					id
					ratingType
					rating
					poolScaling
					resultScaling
					effectScaling
					permanence
					statement
					notes
					sfxs {
						id
					}
					locationsEnabled
					locationsDisabled
					knownTo {
						id
					}
					hidden
					fromEntity {
						id
						name
					}
					toEntity {
						id
						name
					}
					inherited
				}
			}
		}`
		if(apolloClient && trait_setting_id.value && trait_setting_id.value != "placeholder") {
			apolloClient.query({
				query: query,
				variables: {
					traitSettingId: trait_setting_id.value
				},
				fetchPolicy: caching
			}).then((result) => {
				if(result.data.traits[0]) {
					trait.value = {
						...trait.value,
						...result.data.traits[0]
					}
				}
			}).catch((error) => {
				console.error("Error retrieving trait setting for trait ", trait_id.value, ": ", error)
			})
			// const { result } = provideApolloClient(apolloClient)(
			// 	() => useQuery<{traits: Trait[]}>(
			// 		query,
			// 		{ traitSettingId: trait_setting_id.value },
			// 		{ fetchPolicy: 'cache-and-network' }
			// 	)
			// )
			// watch(result, (newResult) => {
			// 	if(newResult?.traits[0].traitSetting) {
			// 		trait.value.traitSetting = newResult.traits[0].traitSetting
			// 	}
			// })
		}
	}

	function retrieve_entities() {
		const query = gql`query TraitInstances($traitId: ID) {
			traits(traitId: $traitId) {
				entities {
					key
					id
					name
				}
			}
		}`
		if(apolloClient) {
			apolloClient.query({
				query: query,
				variables: {
					traitId: trait_id.value
				},
				fetchPolicy: 'cache-first'
			}).then((result) => {
				if(result.data.traits[0].entities) {
					trait.value.entities = result.data.traits[0].entities
				}
			})
			// const { result } = provideApolloClient(apolloClient)(
			// 	() => useQuery<{traits: Trait[]}>(
			// 		query,
			// 		{ traitId: trait_id.value },
			// 		{ fetchPolicy: 'cache-and-network' }
			// 	)
			// )
			// watch(result, (newResult) => {
			// 	if(newResult) {
			// 		trait.value = { ...trait.value, entities: newResult.traits[0].entities }
			// 	}
			// })
		}
	}

	async function retrieve_instances(caching: FetchPolicy = 'cache-first') {
		const query = gql`query TraitInstances($traitId: ID) {
			traits(traitId: $traitId) {
				traitSettings {
					id
					fromEntity {
						id
					}
				}
			}
		}`
		if(apolloClient) {
			apolloClient.query({
				query: query,
				variables: {
					traitId: trait_id.value
				},
				fetchPolicy: caching
			}).then((result) => {
				if(result.data.traits[0].traitSettings) {
					instances.value = result.data.traits[0].traitSettings
				}
			})
			// const { result } = provideApolloClient(apolloClient)(
			// 	() => useQuery(
			// 		query,
			// 		{ traitId: trait_id.value },
			// 		{ fetchPolicy: 'cache-and-network' }
			// 	)
			// )
			// watch(result, (newResult) => {
			// 	if(newResult) {
			// 		instances.value = newResult.traits[0].traitSettings
			// 	}
			// })
		}
	}

	async function mutate_trait(input: TraitInput) {
		const mutate_trait = gql`
			mutation MutateTrait($traitId: ID!, $traitInput: TraitInput!) {
				mutateTrait(traitId: $traitId, traitInput: $traitInput) {
					trait {
						id
						locationRestricted
						possibleSubTraits {
							id
							name
							traitset {
								id
							}
						}
					}
				}
			}`
		// const mutate_setting_trait = gql`
		// 	mutation MutateTraitSetting($traitSettingInput: TraitSettingInput!, $traitSettingId: ID) {
		// 		mutateTraitSetting(traitSettingInput: $traitSettingInput, traitSettingId: $traitSettingId) {
		// 			trait {
		// 				id
		// 			}
		// 		}
		// 	}`
		// const query = trait_setting_id.value ? mutate_setting_trait : mutate_trait
		
		if(apolloClient) {
			await apolloClient.mutate({
				mutation: mutate_trait,
				variables: {
					traitId: trait.value.id,
					traitInput: input
				}
			}).then((result) => {
				if(result.data.mutateTrait.trait) {
					trait.value = {
						...trait.value,
						...result.data.mutateTrait.trait
					}
				}
			})
			// const { mutate } = provideApolloClient(apolloClient)(() => useMutation(mutate_trait))
			// const variables: object = {
			// 	traitId: trait.value.id,
			// 	traitInput: input
			// }
			// console.log("mutating trait: " + trait.value.id + " with variables: ", variables)
			// mutate(variables)
		}
	}

	async function mutate_trait_setting(input: TraitSettingInput) {
		if(!trait_setting_id.value) {
			console.error("mutate_trait_setting called without trait_setting_id")
		}
		const mutate_setting_trait = gql`
			mutation MutateTraitSetting($traitSettingInput: TraitSettingInput!, $traitSettingId: ID) {
				mutateTraitSetting(traitSettingInput: $traitSettingInput, traitSettingId: $traitSettingId) {
					trait {
						id
					}
				}
			}`
		if(apolloClient && trait_setting_id.value) {
			await apolloClient.mutate({
				mutation: mutate_setting_trait,
				variables: {
					traitSettingId: trait_setting_id.value,
					traitSettingInput: input
				}
			})
			await retrieve_trait('network-only')
			retrieve_trait_setting('network-only')
			// const { mutate } = provideApolloClient(apolloClient)(() => useMutation(mutate_setting_trait))
			// let variables: object = {
			// 	traitSettingId: trait_setting_id.value,
			// 	traitSettingInput: input
			// }
			// mutate(variables)
		}
	}

	async function mutate_trait_setting_temp(input: TraitSettingInput, temp: boolean = false) {
		if(!trait_setting_id.value) {
			console.error("mutate_trait_setting called without trait_setting_id")
		}
		const mutate_setting_trait = gql`
			mutation MutateTraitSetting($traitSettingInput: TraitSettingInput!, $traitSettingId: ID, $temp: Boolean) {
				mutateTraitSetting(traitSettingInput: $traitSettingInput, traitSettingId: $traitSettingId, temp: $temp) {
					trait {
						id
					}
				}
			}`
		if(apolloClient && trait_setting_id.value) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(mutate_setting_trait))
			let variables: object = {
				traitSettingId: trait_setting_id.value,
				traitSettingInput: input,
				temp: true
			}
			await mutate(variables)
		}
	}

	async function overwrite_trait(input: TraitSettingInput) {
		const overwrite_query = gql`mutation OverwriteTrait($entityId: ID!, $traitId: ID!, $traitSettingInput: TraitSettingInput) {
			assignTrait(entityId: $entityId, traitId: $traitId, traitSettingInput: $traitSettingInput) {
				trait {
					id
				}
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(overwrite_query))
			let variables: object = {
				entityId: entity_id.value,
				traitId: trait_id.value,
				traitSettingInput: input
			}
			await mutate(variables)
		}
	}

	function copy_trait(trait_setting_input?: TraitSettingInput) {
		const copy_query = gql`mutation CopyTrait($traitSettingId: ID!, $traitSettingInput: TraitSettingInput) {
			cloneTraitSetting(traitSettingId: $traitSettingId, traitSettingInput: $traitSettingInput) {
				trait {
					id
				}
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(copy_query))
			let variables: object = {
				traitSettingId: trait_setting_id.value,
				traitSettingInput: trait_setting_input
			}
			mutate(variables)
		}
	}

	async function change_trait_entity(entity_id: string) {
		const change_entity_query = gql`
			mutation Mutation($traitSettingId: ID, $entityId: ID) {
				mutateTraitSetting(traitSettingId: $traitSettingId, entityId: $entityId) {
					trait {
						id
					}
				}
			}`
		if(apolloClient) {
			await apolloClient.mutate({
				mutation: change_entity_query,
				variables: {
					traitSettingId: trait_setting_id.value,
					entityId: entity_id
				}
			})
			// const { mutate } = provideApolloClient(apolloClient)(() => useMutation(
			// ))
			// mutate({ traitSettingId: trait_setting_id.value, entityId: entity_id })
		}
	}

	function transfer_resource(entity_id: string, die: DieType) {
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(gql`
				mutation TransferResource($traitSettingId: ID, $entityId: ID, $dieType: Int) {
					mutateTraitSetting(traitSettingId: $traitSettingId, entityId: $entityId, dieType: $dieType) {
						trait {
							id
						}
					}
				}`
			))
			console.log("transferring resource: " + trait_setting_id.value + " to " + entity_id + " with dieType: " + die.number_rating)
			mutate({ traitSettingId: trait_setting_id.value, entityId: entity_id, dieType: die.number_rating })
		}
	}

	async function unassign_trait() {
		console.log("unassigning trait: " + trait_setting_id.value)
		const query = gql`
			mutation UnassignTrait($traitSettingId: ID!) {
				unassignTrait(traitSettingId: $traitSettingId) {
					success
				}
			}`
		if(apolloClient && trait_setting_id.value) {
			await apolloClient.mutate({
				mutation: query,
				variables: {
					traitSettingId: trait_setting_id.value
				}
			})
			// const { mutate } = provideApolloClient(apolloClient)(() => useMutation(
			// ))
			// mutate({ traitSettingId: trait_setting_id.value })
		}
	}

	async function retrieve_statement_examples() {
		const query_get_example_statements = gql`query StatementExamples($traitId: ID) {
			traits(traitId: $traitId) {
				statementExamples
			}
		}`
		if(apolloClient && trait_id.value) {
			const { data } = await apolloClient.query({
				query: query_get_example_statements,
				variables: {
					traitId: trait_id.value
				},
				fetchPolicy: 'network-only'
			})
			return data.traits[0].statementExamples
			// let result = <string[]>[]
			// await apolloClient.query({
			// 	query: query_get_example_statements,
			// 	variables: {
			// 		traitId: trait_id.value
			// 	},
			// 	fetchPolicy: 'cache-first'
			// }).then((response) => {
			// 	result = response.data.traits[0].statementExamples
			// 	// console.log("retrieved statement examples: ", result.data.traits[0].statementExamples)
			// 	// return result.data.traits[0].statementExamples
			// }).catch((error) => {
			// 	console.error("error retrieving statement examples: ", error)
			// })
			// return result
			// const { result } = provideApolloClient(apolloClient)(
			// 	() => useQuery(
			// 		query_get_example_statements,
			// 		{ traitId: trait_id.value },
			// 		{ fetchPolicy: 'cache-and-network' }
			// 	)
			// )
			// const newResult = await new Promise(resolve => {
			// 	watch(result, (newResult) => resolve(newResult))
			// })
			// console.log("retrieved statement examples: ", newResult)
			// return newResult.traits[0].statementExamples
		}
		else {
			return []
		}
	}

	function retrieve_possible_sfxs() {
		const query_get_sfxs = gql`query PossibleSFXs($traitId: ID) {
			traits(traitId: $traitId) {
				possibleSfxs {
					id
					name
					description
				}
			}
		}`
		if(apolloClient && trait_id.value) {
			apolloClient.query({
				query: query_get_sfxs,
				variables: {
					traitId: trait_id.value
				},
				fetchPolicy: 'cache-first'
			}).then((result) => {
				trait.value = { ...trait.value, possibleSfxs: result.data.traits[0].possibleSfxs }
			})
			// const { result } = provideApolloClient(apolloClient)(
			// 	() => useQuery(
			// 		query_get_sfxs,
			// 		{ traitId: trait_id.value },
			// 		{ fetchPolicy: 'cache-and-network' }
			// 	)
			// )
			// watch(result, (newResult) => {
			// 	console.log("retrieved possible sfxs: ", JSON.stringify(newResult))
			// 	trait.value = { ...trait.value, possibleSfxs: newResult.traits[0].possibleSfxs }
			// })
		}
	}

	function retrieve_default_settings(caching: FetchPolicy = 'cache-first') {
		const query_get_default_trait = gql`query TraitDefaults($traitId: ID) {
			traits(traitId: $traitId) {
				defaultTraitSetting {
					id
					ratingType
					rating
					poolScaling
					resultScaling
					effectScaling
					locationsEnabled
					locationsDisabled
					sfxs {
						id
					}
					hidden
				}
			}
		}`
		console.log("retrieving default trait for trait: " + trait_id.value)
		let query = query_get_default_trait
		let args: { traitId: string | undefined } = { traitId: trait_id.value }
		if(apolloClient) {
			apolloClient.query({
				query: query,
				variables: args,
				fetchPolicy: caching
			}).then((result) => {
				console.log("retrieved default for trait: " + trait_id.value + ": ")
				console.log(result)
				let convertedRating = <DieType[]>[]
				if (result.data.traits[0].defaultTraitSetting.rating) {
					convertedRating = convert_rating_to_dice(
						result.data.traits[0].defaultTraitSetting.rating,
						result.data.traits[0].defaultTraitSetting.ratingType,
						trait_id.value,
						result.data.traits[0].defaultTraitSetting.id,
						undefined,
						undefined,
						result.data.traits[0].defaultTraitSetting.poolScaling,
						result.data.traits[0].defaultTraitSetting.resultScaling,
						result.data.traits[0].defaultTraitSetting.effectScaling
					)
				}
				default_settings.value = {
					...default_settings.value,
					...result.data.traits[0].defaultTraitSetting,
					rating: convertedRating
				}
				if(!default_settings.value) {
					console.log("no defaults found; setting default settings")
					default_settings.value = {
						ratingType: 'empty',
						rating: [],
						locationsEnabled: [],
						locationsDisabled: [],
						sfxs: []
					}
				}
			})
			// const { result } = provideApolloClient(apolloClient)(
			// 	() => useQuery(
			// 		query,
			// 		args,
			// 		{ fetchPolicy: 'cache-and-network' }
			// 	)
			// )
			// watch(result, (newResult) => {
			// 	console.log(newResult.traits)
			// 	if(newResult && newResult.traits[0].defaultTraitSetting) {
			// 		console.log("retrieved default for trait: " + trait_id.value + ": ")
			// 		console.log(newResult)
			// 		let convertedRating = <DieType[]>[]
			// 		if (newResult.traits[0].defaultTraitSetting.rating) {
			// 			convertedRating = convert_rating_to_dice(
			// 				newResult.traits[0].defaultTraitSetting.rating,
			// 				newResult.traits[0].defaultTraitSetting.ratingType,
			// 				trait_id.value,
			// 				trait_setting_id.value,
			// 				undefined,
			// 				undefined
			// 			)
			// 		}
			// 		default_settings.value = {
			// 			...newResult.traits[0].defaultTraitSetting,
			// 			rating: convertedRating
			// 		}
			// 		if(!default_settings.value) {
			// 			console.log("no defaults found; setting default settings")
			// 			default_settings.value = {
			// 				ratingType: 'empty',
			// 				rating: [],
			// 				locationsEnabled: [],
			// 				locationsDisabled: [],
			// 				sfxs: []
			// 			}
			// 		}
			// 	}
			// })
		}
	}

	function mutate_default_settings(new_defaults: TraitSettingInput) {
		const mutate_update_trait = gql`mutation Mutation($defaultSettings: TraitSettingInput!, $traitId: ID!) {
			updateTraitDefault(defaultSettings: $defaultSettings, traitId: $traitId) {
				trait {
					defaultTraitSetting {
						id
						ratingType
						rating
						locationsEnabled
						locationsDisabled
						sfxs {
							id
						}
						hidden
					}
				}
			}
		}`
		
		if(apolloClient) {
			apolloClient.mutate({
				mutation: mutate_update_trait,
				variables: {
					defaultSettings: new_defaults,
					traitId: trait_id.value
				}
			}).then((result) => {
				default_settings.value = {
					...default_settings.value,
					...result.data.updateTraitDefault.trait.defaultTraitSetting
				}
			})
			// const { mutate } = provideApolloClient(apolloClient)(() => useMutation(mutate_update_trait))
			// let variables: object = {
			// 	traitId: trait_id.value,
			// 	defaultSettings: new_defaults
			// }
			// console.log("updating trait defaults with variables: ", variables)
			// mutate(variables)
		}
	}

	async function assign_subtrait(trait_setting_id: string, subtrait_id: string, _entity_id?: string) {
		if(apolloClient && trait_setting_id && subtrait_id) {
			const query = gql`mutation Mutation($traitSettingId: ID!, $subtraitId: ID!, $entityId: ID) {
				assignSubTrait(traitSettingId: $traitSettingId, subtraitId: $subtraitId, entityId: $entityId) {
					trait {
						id
						subTraits {
							id
							traitSettingId
							rating
						}
					}
				}
			}`
			await apolloClient.mutate({
				mutation: query,
				variables: {
					traitSettingId: trait_setting_id,
					subtraitId: subtrait_id,
					entityId: _entity_id
				}
			}).then((result) => {
				console.log("mergin trait " + JSON.stringify(trait.value) + " with result: " + JSON.stringify(result.data.assignSubTrait.trait))
				if(result.data.assignSubTrait.trait.subTraits && result.data.assignSubTrait.trait.subTraits.length > 0) {
					const new_subTraits = []
					for(const subTrait of result.data.assignSubTrait.trait.subTraits) {
						let new_subTrait = { ...subTrait }
						if(new_subTrait.rating) {
							const new_rating = convert_rating_to_dice(
								new_subTrait.rating, // this is actually a number, as it is retrieved from GraphQL
								new_subTrait.ratingType,
								new_subTrait.id,
								new_subTrait.traitSettingId,
								new_subTrait.traitsetId,
								entity_id.value
							)
							new_subTrait = { ...new_subTrait, rating: new_rating }
						}
						new_subTraits.push(new_subTrait)
					}
					trait.value = {
						...trait.value,
						subTraits: new_subTraits
					}
				}
			})
			// const { mutate } = provideApolloClient(apolloClient)(() => useMutation(gql`
			// 	mutation Mutation($traitSettingId: ID!, $subtraitId: ID!, $entityId: ID) {
			// 		assignSubTrait(traitSettingId: $traitSettingId, subtraitId: $subtraitId, entityId: $entityId) {
			// 			trait {
			// 				id
			// 			}
			// 		}
			// 	}`
			// ))
			// let variables: object = {
			// 	traitSettingId: trait_setting_id,
			// 	subtraitId: subtrait_id,
			// 	entityId: entity_id
			// }
			// console.log("assigning sub-trait: " + subtrait_id + " to trait setting: " + trait_setting_id)
			// mutate(variables)
		}
	}

	async function unassign_subtrait(subtrait_setting_id: string) {
		const query = gql`mutation UnassignSubTrait($traitSettingId: ID, $subtraitSettingId: ID!) {
			unassignSubTrait(traitSettingId: $traitSettingId, subtraitSettingId: $subtraitSettingId) {
				success
			}
		}`
		
		if(apolloClient) {
			console.log("unassigning sub-trait: " + subtrait_setting_id + " from trait setting: " + (trait.value.traitSettingId ?? trait_setting_id.value ?? undefined))
			await apolloClient.mutate({
				mutation: query,
				variables: {
					traitSettingId: (trait.value.traitSettingId ?? trait_setting_id.value ?? undefined),
					subtraitSettingId: subtrait_setting_id
				}
			})
			// const { mutate } = provideApolloClient(apolloClient)(() => useMutation(gql`
			// 	mutation UnassignSubTrait($traitSettingId: ID, $subtraitSettingId: ID!) {
			// 		unassignSubTrait(traitSettingId: $traitSettingId, subtraitSettingId: $subtraitSettingId) {
			// 			success
			// 		}
			// 	}`
			// ))
			// let variables: object = {
			// 	traitSettingId: (trait.value.traitSettingId ?? trait_setting_id.value ?? undefined),
			// 	subtraitSettingId: subtrait_setting_id
			// }
			// mutate(variables)
		}
	}

	async function delete_trait() {
		if(apolloClient && trait_id.value) {
			await apolloClient.mutate({
				mutation: gql`mutation DeleteTrait($traitId: ID!) {
					deleteTrait(traitId: $traitId) {
						success
					}
				}`,
				variables: {
					traitId: trait_id.value
				}
			})
			// const { mutate } = provideApolloClient(apolloClient)(() => useMutation(gql`
			// 	mutation DeleteTrait($traitId: ID!) {
			// 		deleteTrait(traitId: $traitId) {
			// 			success
			// 		}
			// 	}`
			// ))
			// let variables: object = {
			// 	traitId: trait_id.value
			// }
			// mutate(variables)
		}
	}

	return {
		trait_id,
		trait_setting_id,
		entity_id,
		trait,
		default_settings,
		retrieve_trait,
		retrieve_trait_setting,
		retrieve_entities,
		instances,
		retrieve_instances,
		mutate_trait,
		mutate_trait_setting,
		mutate_trait_setting_temp,
		overwrite_trait,
		copy_trait,
		change_trait_entity,
		transfer_resource,
		unassign_trait,
		retrieve_statement_examples,
		retrieve_possible_sfxs,
		retrieve_default_settings,
		mutate_default_settings,
		assign_subtrait,
		unassign_subtrait,
		delete_trait
	}
}
