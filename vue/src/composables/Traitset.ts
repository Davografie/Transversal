/*
	traitset logic
*/
import { ref, watch, inject } from 'vue'
import type { Ref } from 'vue'

import { useQuery, useMutation, provideApolloClient } from "@vue/apollo-composable"
import type { ApolloClient } from '@apollo/client/core'
import gql from 'graphql-tag'

import { useRating } from '@/composables/Rating'
import { placeholder_trait } from '@/composables/Trait'
import type { Traitset, TraitSetting, TraitSettingInput, Die, TraitsetInput } from '@/interfaces/Types'

export const placeholder_traitset: Traitset = {
	id: "placeholder",
	name: "loading",
	traits: [
		placeholder_trait
	]
}

interface sorting_type {
	id: string,
	text: string
}

export const SORTING = <sorting_type[]>[
	{
		id: "RATING",
		text: "rating"
	},
	{
		id: "NAME",
		text: "alphabetical"
	},
]

interface defaultTraitSetting {
	rating?: Die[]
	locationsEnabled?: string[]
	locationsDisabled?: string[]
	sfxs?: string[]
}

interface default_trait_data {
	traitsets: [{
		defaultTraitSetting: {
			rating: number[],
			locationsEnabled: string[],
			locationsDisabled: string[],
			sfxs: string[]
		}
	}]
}

export function useTraitset(init?: Traitset, traitset_id?: string, entity_id?: string, sorting_id?: string) {
	const traitset: Ref<Traitset> = ref(init ?? placeholder_traitset)
	const default_settings: Ref<TraitSetting|undefined> = ref()
	const sorting: Ref<sorting_type> = ref(SORTING.find(s => s.id == sorting_id) ?? (SORTING && SORTING[0]) ?? {})
	const apolloClient = inject<ApolloClient<Cache>>('apolloClient')

	function set_entity(_id: string) {
		entity_id = _id
	}

	function set_traitset_id(_id: string) {
		traitset_id = _id
	}

	function retrieve_traitset() {
		if(!traitset_id && !traitset.value.id || (traitset_id ?? traitset.value.id) == "placeholder") {
			console.warn("no traitset id provided")
		}
		else {
			const query_get_traitset = gql`query TraitsetByID($traitsetId: ID, $sorting: String) {
				traitsets(traitsetId: $traitsetId, sorting: $sorting) {
					id
					name
					explainer
					entityTypes
					locationRestricted
					sfxs {
						id
						name
					}
					limit
					duplicates
					traits {
						id
						name
					}
				}
			}`
			const query_get_entity_traitset = gql`query TraitsetForEntity($traitsetId: ID, $entityId: ID, $sorting: String) {
				traitsets(traitsetId: $traitsetId, entityId: $entityId, sorting: $sorting) {
					id
					name
					explainer
					entityTypes
					duplicates
					sfxs {
						id
					}
					traits {
						id
						traitSettingId
						name
						rating
						inheritable
						subTraits {
							traitSettingId
						}
						requiredTraits {
							id
						}
						traitSetting {
							knownTo {
								id
							}
							statement
							hidden
							priority
						}
					}
				}
			}`
			let query = query_get_traitset
			let args: { traitsetId: string, entityId?: string, sorting?: string } = { traitsetId: traitset_id ?? traitset.value.id, sorting: sorting.value.id }
			// console.log("retrieving traitset: " + traitset_id + ", entity_id: " + entity_id + ", sorting: " + Sorting.NAME.toString())
			if(entity_id) {
				query = query_get_entity_traitset
				args.entityId = entity_id
			}
			// console.log("query: " + query + ", args: " + JSON.stringify(args))
			if(apolloClient) {
				const { result } = provideApolloClient(apolloClient)(
					() => useQuery<{traitsets: Traitset[]}>(
						query,
						args,
						{ fetchPolicy: 'cache-and-network' }
					)
				)
				watch(result, (newResult) => {
					if(newResult && newResult.traitsets.length > 0) {
						// console.log("retrieved traitset: ")
						// console.log(newResult)
						traitset.value = newResult.traitsets[0]
					}
				})
			}
		}
	}

	function retrieve_default_settings() {
		// this should probably be an asynchronous function
		const query_get_default_trait = gql`query RetrieveTraitsetDefaults($traitsetId: ID) {
			traitsets(traitsetId: $traitsetId) {
				defaultTraitSetting {
					ratingType
					rating
					locationsEnabled
					locationsDisabled
					sfxs {
						id
					}
					sfxsIds
					hidden
				}
			}
		}`
		// console.log("retrieving default trait for traitset: " + traitset_id)
		let query = query_get_default_trait
		let args: { traitsetId: string | undefined } = { traitsetId: traitset_id }
		// console.log("query: " + query + ", args: " + JSON.stringify(args))
		if(apolloClient) {
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery<default_trait_data>(
					query,
					args,
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			watch(result, (newResult) => {
				if(newResult) {
					// console.log("retrieved default trait for traitset: " + JSON.stringify(newResult.traitsets[0].defaultTraitSetting))
					const { convert_rating_to_dice } = useRating()
					const default_rating = convert_rating_to_dice(
						newResult.traitsets[0].defaultTraitSetting.rating,
						newResult.traitsets[0].defaultTraitSetting.ratingType,
						undefined,
						undefined,
						traitset_id,
						undefined
					)
					// console.log(default_rating)
					default_settings.value = {
						...default_settings.value,
						...newResult.traitsets[0].defaultTraitSetting,
						rating: default_rating
					}
				}
			})
		}
	}

	function mutate_traitset(traitset_input: TraitsetInput) {
		const query = gql`mutation MutateTraitset(
			$traitsetId: ID!,
			$traitsetInput: TraitsetInput!
		) {
			mutateTraitset(
				traitsetId: $traitsetId,
				traitsetInput: $traitsetInput
			) {
				message
				traitset {
					id
					name
				}
			}
		}`
		
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(query))
			let variables: object = {
				traitsetId: traitset.value.id,
				traitsetInput: traitset_input
			}
			console.log("updating traitset with variables: ", variables)
			mutate(variables)
		}
	}

	function mutate_default_settings(new_defaults: TraitSettingInput) {
		const mutate_update_traitset = gql`mutation updateTraitsetDefault($defaultSettings: TraitSettingInput!, $traitsetId: ID!) {
			updateTraitsetDefault(defaultSettings: $defaultSettings, traitsetId: $traitsetId) {
				traitset {
					name
					defaultTraitSetting {
						rating
					}
				}
			}
		}`
		
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(mutate_update_traitset))
			let variables: object = {
				traitsetId: traitset_id,
				defaultSettings: new_defaults
			}
			console.log("updating traitset with variables: ", variables)
			mutate(variables)
		}
	}

	function update_traitset_settings(new_settings: any) {
		const mutate_update_traitset = gql`mutation updateTraitsetSetting($entityId: ID, $traitsetId: ID, $traitsetSettingInput: TraitsetSettingInput!) {
			updateTraitsetSetting(entityId: $entityId, traitsetId: $traitsetId, traitsetSettingInput: $traitsetSettingInput) {
				traitsetSetting {
					id
				}
			}
		}`
		
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(mutate_update_traitset))
			let variables: object = {
				entityId: entity_id,
				traitsetId: traitset_id,
				traitsetSettingInput: new_settings
			}
			console.log("updating traitset with variables: ", variables)
			mutate(variables)
		}
	}

	interface trait_input_type {
		name?: string
		traitsetId?: string
		defaultRating?: string[]
	}

	function create_trait(name: string) {
		const mutate_create_trait = gql`
			mutation CreateTrait($traitInput: TraitInput!) {
				createTrait(traitInput: $traitInput) {
					trait {
						id
					}
				}
			}`
		
		if(apolloClient) {
			const { mutate, onDone, onError } = provideApolloClient(apolloClient)(() => useMutation(mutate_create_trait))
			let trait_setting_input: trait_input_type = {
				"name": name,
				"traitsetId": traitset.value.id
			}
			console.log("creating trait for traitset: " + traitset.value.id + " with variables: ", trait_setting_input)
			mutate({traitInput: trait_setting_input})
				.then((response) => {
					console.log(response)
					const new_trait = response?.data?.mutateTrait?.trait
					console.log('new trait: ', new_trait)

					// Automatically assign the trait if entity_id is set
					if (entity_id && new_trait?.id) {
						assign_trait(new_trait.id)
					}
				})
				.catch((error) => {
					console.error('Error creating trait:', error)
				})
			// console.log("new trait: ", new_trait)
		}
	}


	async function assign_trait(trait_id: string, location_id?: string, trait_setting_input?: TraitSettingInput) {
		const mutate_assign_trait = gql`mutation AssignTrait($traitId: ID!, $entityId: ID!, $locationId: ID, $traitSettingInput: TraitSettingInput) {
			assignTrait(traitId: $traitId, entityId: $entityId, locationId: $locationId, traitSettingInput: $traitSettingInput) {
				trait {
					id
				}
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(mutate_assign_trait))
			let variables: object = {
				traitId: trait_id,
				entityId: entity_id,
				locationId: location_id,
				traitSettingInput: trait_setting_input
			}
			
			console.log("assigning trait with variables: ", variables)
			await mutate(variables)
			retrieve_traitset()
		}
	}

	async function assign_locationrestricted_trait(trait_id: string, location_id: string) {
		const mutate_assign_trait = gql`mutation AssignTraitLocRestr($traitId: ID!, $entityId: ID!, $locationId: ID) {
			assignTrait(traitId: $traitId, entityId: $entityId, locationId: $locationId) {
				trait {
					id
				}
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(mutate_assign_trait))
			let variables: object = {
				traitId: trait_id,
				entityId: entity_id,
				locationId: location_id
			}
			
			console.log("assigning trait with variables: ", variables)
			await mutate(variables)
			retrieve_traitset()
		}
	}

	function delete_traitset() {
		const mutate_delete_traitset = gql`mutation DeleteTraitset($traitsetId: ID!) {
			deleteTraitset(traitsetId: $traitsetId) {
				message
				success
			}
		}`
		
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(mutate_delete_traitset))
			let variables: object = {
				traitsetId: traitset_id
			}
			console.log("deleting traitset with variables: ", variables)
			mutate(variables)
		}
	}

	return {
		traitset,
		retrieve_traitset,
		mutate_traitset,
		update_traitset_settings,
		default_settings,
		retrieve_default_settings,
		create_trait,
		assign_trait,
		assign_locationrestricted_trait,
		mutate_default_settings,
		set_entity,
		set_traitset_id,
		sorting,
		delete_traitset
	}
}
