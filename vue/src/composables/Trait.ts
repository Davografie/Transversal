/*
	Trait logic
*/
import _ from "lodash"

import { ref, watch, inject } from "vue"
import type { Ref } from "vue"

import type { ApolloClient } from '@apollo/client/core'
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

export const rating_types: string[] = ['empty', 'static', 'resource', 'challenge']


export function useTrait(init?: Trait, _trait_id?: string, _trait_setting_id?: string, _entity_id?: string) {
	const apolloClient = inject<ApolloClient<Cache>>('apolloClient')
	
	const trait: Ref<Trait> = ref(init ?? placeholder_trait)
	const default_settings: Ref<TraitSetting|undefined> = ref()

	const trait_id = ref(_trait_id)
	const trait_setting_id = ref(_trait_setting_id)
	const entity_id = ref(_entity_id)
	const instances: Ref<string[]> = ref([])

	function retrieve_trait() {
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
					locationsEnabled
					locationsDisabled
					knownTo {
						id
					}
					hidden
					fromEntity {
						id
					}
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
				sfxs {
					id
				}
				subTraits {
					id
					traitSettingId
					rating
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
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery<{traits: Trait[]}>(
					query,
					args,
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			watch(result, (newResult) => {
				if(newResult && newResult.traits?.length > 0) {
					let newTrait = newResult.traits[0]
					if(newResult.traits[0].rating) {
						const new_rating = convert_rating_to_dice(
							newResult.traits[0].rating, // this is actually a number, as it is retrieved from GraphQL
							newResult.traits[0].ratingType,
							newResult.traits[0].id,
							newResult.traits[0].traitSettingId,
							newResult.traits[0].traitsetId,
							entity_id.value
						)
						newTrait = {
							...newTrait,
							rating: new_rating
						}
					}
					if(newResult.traits[0].subTraits) {
						let newSubTraits = <Trait[]>[]
						for(let i = 0; i < newResult.traits[0].subTraits.length; i++) {
							let newSubTrait = newResult.traits[0].subTraits[i]
							if(newResult.traits[0].subTraits[i].rating) {
								const new_rating = convert_rating_to_dice(
									newResult.traits[0].subTraits[i].rating, // this is actually a number, as it is retrieved from GraphQL
									newResult.traits[0].subTraits[i].ratingType,
									newResult.traits[0].subTraits[i].id,
									newResult.traits[0].subTraits[i].traitSettingId,
									newResult.traits[0].subTraits[i].traitsetId,
									entity_id.value
								)
								newSubTrait = {
									...newSubTrait,
									rating: new_rating
								}
								newSubTraits.push(newSubTrait)
							}
						}
						newTrait = {
							...newTrait,
							subTraits: newSubTraits
						}
					}
					trait.value = newTrait
				}
			})
		}
	}

	const { convert_rating_to_dice } = useRating()

	function retrieve_trait_setting() {
		const query = gql`query TraitSettingByID($traitSettingId: ID) {
			traits(traitSettingId: $traitSettingId) {
				traitSetting {
					id
					ratingType
					rating
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
				}
			}
		}`
		if(apolloClient && trait_setting_id.value && trait_setting_id.value != "placeholder") {
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery<{traits: Trait[]}>(
					query,
					{ traitSettingId: trait_setting_id.value },
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			watch(result, (newResult) => {
				if(newResult?.traits[0].traitSetting) {
					trait.value.traitSetting = newResult.traits[0].traitSetting
				}
			})
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
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery<{traits: Trait[]}>(
					query,
					{ traitId: trait_id.value },
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			watch(result, (newResult) => {
				if(newResult) {
					trait.value = { ...trait.value, entities: newResult.traits[0].entities }
				}
			})
		}
	}

	function retrieve_instances() {
		const query = gql`query TraitInstances($traitId: ID) {
			traits(traitId: $traitId) {
				traitSettings {
					id
				}
			}
		}`
		if(apolloClient) {
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery(
					query,
					{ traitId: trait_id.value },
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			watch(result, (newResult) => {
				if(newResult) {
					instances.value = newResult.traits[0].traitSettings.map((traitSetting: TraitSetting) => traitSetting.id)
				}
			})
		}
	}

	async function mutate_trait(input: TraitInput) {
		const mutate_trait = gql`
			mutation MutateTrait($traitId: ID!, $traitInput: TraitInput!) {
				mutateTrait(traitId: $traitId, traitInput: $traitInput) {
					trait {
						id
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
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(mutate_trait))
			const variables: object = {
				traitId: trait.value.id,
				traitInput: input
			}
			console.log("mutating trait: " + trait.value.id + " with variables: ", variables)
			mutate(variables)
		}
	}

	function mutate_trait_setting(input: TraitSettingInput) {
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
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(mutate_setting_trait))
			let variables: object = {
				traitSettingId: trait_setting_id.value,
				traitSettingInput: input
			}
			mutate(variables)
		}
	}

	function overwrite_trait(input: TraitSettingInput) {
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
			mutate(variables)
		}
	}

	function copy_trait(trait_setting_input: TraitSettingInput) {
		const copy_query = gql`mutation CopyTrait($traitSettingInput: TraitSettingInput!, $traitId: ID!, $entityId: ID!) {
			assignTrait(traitSettingInput: $traitSettingInput, traitId: $traitId, entityId: $entityId) {
				trait {
					id
				}
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(copy_query))
			let variables: object = {
				traitSettingInput: trait_setting_input,
				traitId: trait_id.value,
				entityId: entity_id.value
			}
			mutate(variables)
		}
	}

	function change_trait_entity(entity_id: string) {
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(gql`
				mutation Mutation($traitSettingId: ID, $entityId: ID) {
					mutateTraitSetting(traitSettingId: $traitSettingId, entityId: $entityId) {
						trait {
							id
						}
					}
				}`
			))
			mutate({ traitSettingId: trait_setting_id.value, entityId: entity_id })
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

	function unassign_trait() {
		console.log("unassigning trait: " + trait_setting_id.value)
		if(apolloClient && trait_setting_id.value) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(gql`
				mutation UnassignTrait($traitSettingId: ID!) {
					unassignTrait(traitSettingId: $traitSettingId) {
						success
					}
				}`
			))
			mutate({ traitSettingId: trait_setting_id.value })
		}
	}

	async function retrieve_statement_examples() : Promise<string[]> {
		const query_get_example_statements = gql`query StatementExamples($traitId: ID) {
			traits(traitId: $traitId) {
				statementExamples
			}
		}`
		if(apolloClient && trait_id.value) {
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery(
					query_get_example_statements,
					{ traitId: trait_id.value },
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			const newResult = await new Promise(resolve => {
				watch(result, (newResult) => resolve(newResult))
			})
			console.log("retrieved statement examples: ", newResult)
			return newResult.traits[0].statementExamples
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
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery(
					query_get_sfxs,
					{ traitId: trait_id.value },
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			watch(result, (newResult) => {
				console.log("retrieved possible sfxs: ", JSON.stringify(newResult))
				trait.value = { ...trait.value, possibleSfxs: newResult.traits[0].possibleSfxs }
			})
		}
	}

	function retrieve_default_settings() {
		const query_get_default_trait = gql`query TraitDefaults($traitId: ID) {
			traits(traitId: $traitId) {
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
		}`
		console.log("retrieving default trait for trait: " + trait_id.value)
		let query = query_get_default_trait
		let args: { traitId: string | undefined } = { traitId: trait_id.value }
		if(apolloClient) {
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery(
					query,
					args,
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			watch(result, (newResult) => {
				console.log(newResult.traits)
				if(newResult && newResult.traits[0].defaultTraitSetting) {
					console.log("retrieved default for trait: " + trait_id.value + ": ")
					console.log(newResult)
					let convertedRating = <DieType[]>[]
					if (newResult.traits[0].defaultTraitSetting.rating) {
						convertedRating = convert_rating_to_dice(
							newResult.traits[0].defaultTraitSetting.rating,
							newResult.traits[0].defaultTraitSetting.ratingType,
							trait_id.value,
							trait_setting_id.value,
							undefined,
							undefined
						)
					}
					default_settings.value = {
						...newResult.traits[0].defaultTraitSetting,
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
				}
			})
		}
	}

	function mutate_default_settings(new_defaults: TraitSettingInput) {
		const mutate_update_trait = gql`mutation Mutation($defaultSettings: TraitSettingInput!, $traitId: ID!) {
			updateTraitDefault(defaultSettings: $defaultSettings, traitId: $traitId) {
				trait {
					name
					defaultTraitSetting {
						rating
					}
				}
			}
		}`
		
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(mutate_update_trait))
			let variables: object = {
				traitId: trait_id.value,
				defaultSettings: new_defaults
			}
			console.log("updating trait defaults with variables: ", variables)
			mutate(variables)
		}
	}

	function assign_subtrait(trait_setting_id: string, subtrait_id: string, entity_id?: string) {
		if(apolloClient && trait_setting_id && subtrait_id) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(gql`
				mutation Mutation($traitSettingId: ID!, $subtraitId: ID!, $entityId: ID) {
					assignSubTrait(traitSettingId: $traitSettingId, subtraitId: $subtraitId, entityId: $entityId) {
						trait {
							id
						}
					}
				}`
			))
			let variables: object = {
				traitSettingId: trait_setting_id,
				subtraitId: subtrait_id,
				entityId: entity_id
			}
			console.log("assigning sub-trait: " + subtrait_id + " to trait setting: " + trait_setting_id)
			mutate(variables)
		}
	}

	function unassign_subtrait(subtrait_setting_id: string) {
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(gql`
				mutation UnassignSubTrait($traitSettingId: ID, $subtraitSettingId: ID!) {
					unassignSubTrait(traitSettingId: $traitSettingId, subtraitSettingId: $subtraitSettingId) {
						success
					}
				}`
			))
			let variables: object = {
				traitSettingId: (trait.value.traitSettingId ?? trait_setting_id.value ?? undefined),
				subtraitSettingId: subtrait_setting_id
			}
			mutate(variables)
		}
	}

	function delete_trait() {
		if(apolloClient && trait_id.value) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(gql`
				mutation DeleteTrait($traitId: ID!) {
					deleteTrait(traitId: $traitId) {
						success
					}
				}`
			))
			let variables: object = {
				traitId: trait_id.value
			}
			mutate(variables)
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
