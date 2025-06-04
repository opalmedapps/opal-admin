// eslint-disable-next-line max-len
// SPDX-FileCopyrightText: Copyright 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/* eslint-disable no-console */
/**
 * @file Utility for Firebase to initialize users for our test/demo data.
 *
 * This file is included in this project for ease of maintenance in tandem with the insert_test_data management command.
 * You can use the listener container to execute this file via:
 * docker compose exec listener sh -c "cd src/firebase && node -e \"$(cat initialize_firebase_users.js)\""
 */
/* eslint-disable import/no-unresolved */
const { getAuth } = require('firebase-admin/auth');

const { FIREBASE_CONFIG } = require('../environment');
const { Firebase } = require('./firebase');

const USER_RECORDS = [
    {
        email: 'laurie@opalmedapps.ca',
        password: '12345Ohig!!',
        uid: 'a51fba18-3810-4808-9238-4d0e487785c8',
    },
    {
        email: 'rory@opalmedapps.ca',
        password: 'Patient.Demo1',
        uid: 'mouj1pqpXrYCl994oSm5wtJT3In2',
    },
    {
        email: 'cara@opalmedapps.ca',
        password: 'Patient.Demo1',
        uid: 'dR2Cb1Yf0vQb4ywvMoAXw1SxbY93',
    },
    {
        email: 'john@opalmedapps.ca',
        password: '12345Ohig!!',
        uid: 'hIMnEXkedPMxYnXeqNXzphklu4V2',
    },
    {
        email: 'richard@opalmedapps.ca',
        password: '12345Ohig!!',
        uid: '2WhxeTpYF8aHlfSQX8oGeq4LFhw2',
    },
    {
        email: 'mike@opalmedapps.ca',
        password: 'Patient.Demo1',
        uid: 'hSJdAae7xWNwnemd2YypQSVfoOb2',
    },
    {
        email: 'kathy@opalmedapps.ca',
        password: 'Patient.Demo1',
        uid: 'OPWj4Cj5iRfgva4b3HGtVGjvuk13',
    },
    {
        email: 'valerie@opalmedapps.ca',
        password: 'Patient.Demo1',
        uid: 'dcBSK5qdoiOM2L9cEdShkqOadkG3',
    },
    {
        email: 'pete@opalmedapps.ca',
        password: 'Patient.Demo1',
        uid: '9kmS7qYQX8arnFFs4ZYJk1tqLFw1',
    },
    {
        email: 'martin@opalmedapps.ca',
        password: 'Patient.Demo1',
        uid: '2grqcCoyPlVucfAPD4NM1SuCk3i1',
    },
    // A user registered at another institution
    {
        email: 'apptest+ned@opalmedapps.ca',
        password: '12345Ohig!!',
        uid: '9wajsHGHaMUdDIcepyUJkm4O1pG3',
    },
];

/**
 * @description Deletes all Firebase users.
 * @returns {Promise<void>} Rejects with an error if listing or deleting Firebase users fails.
 */
async function deleteAllUsers() {
    // avoid recursion with async/await here and get the max possible number of users
    // to support any number of users the following can be adapted using async/await
    // https://dev.to/pratik14/deleting-all-firebase-users-l4d
    const userRecords = await getAuth().listUsers(1000);
    const uids = userRecords.users.map(userRecord => userRecord.uid);

    await getAuth().deleteUsers(uids);
    console.log('Deleted all users');
}

/**
 * @description Creates a defined list of new Firebase users.
 * @returns {Promise<void>}
 */
async function deleteUsers() {
    for (const user of USER_RECORDS) {
        try {
            // eslint-disable-next-line no-await-in-loop
            await getAuth().deleteUser(user.uid);
            console.log('Successfully deleted user:', user.email);
        }
        catch (error) {
            console.log('Error deleting user:', user.email, error);
        }
    }
}

/**
 * @description Creates a defined list of new Firebase users.
 * @returns {Promise<void>}
 */
async function createUsers() {
    for (const user of USER_RECORDS) {
        try {
            // eslint-disable-next-line no-await-in-loop
            const userRecord = await getAuth().createUser(user);
            console.log('Successfully created new user:', userRecord.email);
        }
        catch (error) {
            console.log('Error creating new user:', error);
        }
    }
}

/**
 * @description Delete all Firebase users and create a pre-defined list of new users.
 * @param {boolean} [shouldDeleteAllUsers] Whether to delete all users before creating new ones,
 * if false, only the pre-defined users will be deleted.
 * @returns {Promise<void>} Rejects with an error if any error occurs
 */
async function run(shouldDeleteAllUsers) {
    const firebase = new Firebase(FIREBASE_CONFIG);
    await firebase.init();

    if (shouldDeleteAllUsers) {
        await deleteAllUsers();
    }
    else {
        await deleteUsers();
    }
    await createUsers();
    process.exit(0);
}

let shouldDeleteAllUsers = false;

if (process.argv.includes('--delete-all-users')) {
    shouldDeleteAllUsers = true;
}

run(shouldDeleteAllUsers);
