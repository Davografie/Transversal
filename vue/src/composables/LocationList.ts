/*
    list of locations for location overview
    allows GMs to set location scope
*/
import { ref, inject, watch, onMounted } from 'vue'
import type { Ref } from 'vue'
import { provideApolloClient, useMutation, useQuery } from '@vue/apollo-composable'
import gql from 'graphql-tag'
import type { ApolloClient } from '@apollo/client'
import { placeholder_location } from '@/composables/Location'
import type { Location } from '@/interfaces/Types'

export function useLocationList(init?: Location[], locales?: boolean, zones?: boolean) {
    const locations: Ref<Location[]> = ref([placeholder_location])
    function retrieve_locations() {
        const get_locations_query = gql`{
            locations {
                id
                key
                name
                zones {
                    id
                    key
                    name
                }
            }
        }`
        const apolloClient: ApolloClient<any>|undefined = inject('apolloClient')
        if(apolloClient) {
            const { result } = provideApolloClient(apolloClient)(
                () => useQuery<{locations: Location[]}>(get_locations_query)
            )
            watch(result, (newResult) => {
                if(newResult) {
                    locations.value = newResult.locations
                }
            },
            { immediate: true })
        }
    }

    onMounted(() => {
        retrieve_locations()
    })
    return { locations }
}
