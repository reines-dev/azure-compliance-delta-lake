param logicAppName string
param location string = resourceGroup().location
param functionAppName string

resource logicApp 'Microsoft.Logic/workflows@2019-05-01' = {
  name: logicAppName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    state: 'Enabled'
    definition: {
      '$schema': 'https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#'
      contentVersion: '1.0.0.0'
      parameters: {
        functionBaseUrl: {
          type: 'String'
          defaultValue: 'https://${functionAppName}.azurewebsites.net/api'
        }
        sources: {
          type: 'Array'
          defaultValue: [
            'ofac'
            'onu'
            'sat69b'
            'ue'
            'dea'
            'lpb'
            'iraq'
          ]
        }
      }
      triggers: {
        Daily_10AM_Recurrence: {
          recurrence: {
            frequency: 'Day'
            interval: 1
            schedule: {
              hours: [
                10
              ]
              minutes: [
                0
              ]
            }
          }
          type: 'Recurrence'
        }
      }
      actions: {
        Process_All_Sources: {
          type: 'Foreach'
          foreach: '@parameters(\'sources\')'
          actions: {
            Step_1_Ingest: {
              type: 'Http'
              inputs: {
                method: 'POST'
                uri: '@{parameters(\'functionBaseUrl\')}/etl/ingest/@{item()}'
                authentication: {
                  type: 'ManagedServiceIdentity'
                }
              }
            }
            Step_2_Transform: {
              type: 'Http'
              inputs: {
                method: 'POST'
                uri: '@{parameters(\'functionBaseUrl\')}/etl/transform/@{item()}'
                authentication: {
                  type: 'ManagedServiceIdentity'
                }
              }
              runAfter: {
                Step_1_Ingest: [
                  'Succeeded'
                ]
              }
            }
            Step_3_Load: {
              type: 'Http'
              inputs: {
                method: 'POST'
                uri: '@{parameters(\'functionBaseUrl\')}/etl/load/@{item()}'
                authentication: {
                  type: 'ManagedServiceIdentity'
                }
              }
              runAfter: {
                Step_2_Transform: [
                  'Succeeded'
                ]
              }
            }
          }
          runAfter: {}
        }
      }
    }
  }
}

output logicAppPrincipalId string = logicApp.identity.principalId
