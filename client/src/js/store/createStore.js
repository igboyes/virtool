/**
 *
 *
 * @copyright 2017 Government of Canada
 * @license MIT
 * @author igboyes
 *
 */

import { createStore, combineReducers, applyMiddleware } from "redux";
import createSagaMiddleware from "redux-saga";

import { virusesReducer } from "../reducers/viruses";
import { accountReducer } from "../reducers/account";
import { rootSaga } from "../sagas/root";
import { watchViruses } from "../sagas/viruses"
import { watchAccount } from "../sagas/account"

const sagaMiddleware = createSagaMiddleware();

const reducer = combineReducers({
    viruses: virusesReducer,
    account: accountReducer
});

export const store = createStore(
    reducer,
    applyMiddleware(sagaMiddleware)
);

sagaMiddleware.run(watchViruses);
sagaMiddleware.run(watchAccount);
