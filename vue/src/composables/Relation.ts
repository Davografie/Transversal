import { ref, type Ref, inject, watch } from 'vue'
import { provideApolloClient, useMutation, useQuery } from '@vue/apollo-composable'
import gql from 'graphql-tag'
import type { ApolloClient } from '@apollo/client'
import type { Relation } from '@/interfaces/Types'

export function useRelation(init?: Relation, relation_id?: string) {
	const apolloClient: ApolloClient<any>|undefined = inject('apolloClient')
	const relation: Ref<Relation> = ref(init || {} as Relation)

	function set_relation_id(id: string) {
		relation.value = {}
		relation_id = id
		retrieve_relation()
	}

	function retrieve_relation() {
		if(apolloClient) {
			const query_get_character = gql`
			query Relations($relationId: ID) {
				relations(relationId: $relationId) {
					id
					fromEntity {
						id
						key
						entityType
						name
					}
					toEntity {
						id
						key
						entityType
						name
					}
					traitsets {
						id
						traits {
							id
							traitSettingId
						}
					}
					favorite
				}
			}`
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery<{relations: Relation[]}>(
					query_get_character,
					{ relationId: relation_id },
					{ fetchPolicy: 'no-cache' }
				)
			)
			watch(result, (newResult) => {
				console.log('retrieved relation: ')
				console.log(newResult)
				if(newResult && newResult.relations.length > 0) {
					relation.value = newResult.relations[0]
				}
			})
		}
	}

	function update_relation(favorite: boolean) {
		if(apolloClient) {
			const mutation_update_relation = gql`mutation UpdateRelation($favorite: Boolean!, $updateRelationId: ID!) {
					updateRelation(favorite: $favorite, id: $updateRelationId) {
						relation {
							id
						}
					}
				}`
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(mutation_update_relation))
			mutate({
				favorite: favorite,
				updateRelationId: relation.value.id
			})
		}
		retrieve_relation()
	}

	function delete_relation() {
		if(apolloClient && relation.value.id) {
			const mutation_delete_relation = gql`mutation DeleteRelation($relationId: ID!) {
				deleteRelation(relationId: $relationId) {
					success
				}
			}`
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(mutation_delete_relation))
			mutate({
				relationId: relation.value.id
			})
		}
	}

	return {
		relation,
		set_relation_id,
		retrieve_relation,
		update_relation,
		delete_relation
	}
}
