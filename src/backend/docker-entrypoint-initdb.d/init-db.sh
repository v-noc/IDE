#!/bin/sh
set -e

# Wait for ArangoDB to be ready
for i in `seq 30`; do
  arangosh --server.endpoint tcp://127.0.0.1:8529 --server.authentication false --javascript.execute-string "db._version()" > /dev/null 2>&1 && break
  echo "Waiting for ArangoDB..."
  sleep 1
done


# Create the application user and database
arangosh --server.endpoint tcp://127.0.0.1:8529 --server.username root --server.password "$ARANGO_ROOT_PASSWORD" --javascript.execute-string "
  try {
    db._createDatabase('$ARANGO_DB');
    console.log('Database \"$ARANGO_DB\" created.');
  } catch (e) {
    if (e.errorNum !== 1207) { // 1207 is 'duplicate name'
      throw e;
    }
    console.log('Database \"$ARANGO_DB\" already exists.');
  }

  try {
    require('@arangodb/users').save('$ARANGO_USER', '$ARANGO_PASSWORD');
    console.log('User \"$ARANGO_USER\" created.');
  } catch (e) {
    if (e.errorNum !== 1600) { // 1600 is 'user already exists'
      throw e;
    }
    console.log('User \"$ARANGO_USER\" already exists.');
  }

  require('@arangodb/users').grantDatabase('$ARANGO_USER', '$ARANGO_DB', 'rw');
  console.log('User \"$ARANGO_USER\" granted access to database \"$ARANGO_DB\".');
"

