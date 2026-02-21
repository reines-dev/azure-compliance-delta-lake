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
        Step_1_Ingest_OFAC: {
          type: 'Http'
          inputs: {
            method: 'POST'
            uri: '@{parameters(\'functionBaseUrl\')}/etl/ingest/ofac'
            authentication: {
              type: 'ManagedServiceIdentity'
            }
          }
          runAfter: {}
        }
        Step_2_Ingest_SAT69B: {
          type: 'Http'
          inputs: {
            method: 'POST'
            uri: '@{parameters(\'functionBaseUrl\')}/etl/ingest/sat69b'
            authentication: {
              type: 'ManagedServiceIdentity'
            }
          }
          runAfter: {
            Step_1_Ingest_OFAC: [
              'Succeeded'
            ]
          }
        }
        Step_3_Transform_All: {
          type: 'Http'
          inputs: {
            method: 'POST'
            uri: '@{parameters(\'functionBaseUrl\')}/etl/transform/ofac'
            authentication: {
              type: 'ManagedServiceIdentity'
            }
          }
          runAfter: {
            Step_2_Ingest_SAT69B: [
              'Succeeded'
            ]
          }
        }
        Step_4_Load_Final: {
          type: 'Http'
          inputs: {
            method: 'POST'
            uri: '@{parameters(\'functionBaseUrl\')}/etl/load/ofac'
            authentication: {
              type: 'ManagedServiceIdentity'
            }
          }
          runAfter: {
            Step_3_Transform_All: [
              'Succeeded'
            ]
          }
        }
      }
    }
  }
}

output logicAppPrincipalId string = logicApp.identity.principalId
