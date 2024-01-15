import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import time
import math
from urllib.request import urlopen
import json
import requests
import plotly.graph_objects as go 

import os

import warnings
warnings.filterwarnings("ignore")



def main() :

    @st.cache
    def load_data():
        #file_path = os.getcwd()
        #PATH = file_path+'/data/'
        #données nettoyés
        
        #data_cleaned = pd.read_parquet(PATH+'app_data_cleaned.parquet')
        data_cleaned = pd.read_parquet('app_data_cleaned.parquet')

        #Données de test avant transformation 
        test_X = pd.read_parquet('test_X_NoTransformed.parquet')
    
        #Données de test après transformation
        test_X_transformed = pd.read_parquet('test_X_transformed.parquet')



        #description des features
        description = pd.read_csv('HomeCredit_columns_description.csv', usecols=['Row', 'Description'], index_col=0, encoding='unicode_escape')

        return data_cleaned, test_X, test_X_transformed, description
        #return data_cleaned

    
    @st.cache
    def load_model():
        '''loading the trained model'''
        return pickle.load(open('HistGB_clf_model.pkl', 'rb'))

    @st.cache
    def get_client_info(df, id_client):
        client_info = df[df['SK_ID_CURR']==int(id_client)]
        return client_info


    #@st.cache
    def plot_distribution(applicationDF,feature, client_feature_val, title):

        if (not (math.isnan(client_feature_val))):
            fig = plt.figure(figsize = (10, 4))

            t0 = applicationDF.loc[applicationDF['TARGET'] == 0]
            t1 = applicationDF.loc[applicationDF['TARGET'] == 1]

            if (feature == "DAYS_BIRTH"):
                sns.kdeplot((t0[feature]/-365).dropna(), label = 'Remboursé', color='g')
                sns.kdeplot((t1[feature]/-365).dropna(), label = 'Défaillant', color='r')
                plt.axvline(float(client_feature_val/-365), \
                            color="blue", linestyle='--', label = 'Position Client')

            elif (feature == "DAYS_EMPLOYED"):
                sns.kdeplot((t0[feature]/365).dropna(), label = 'Remboursé', color='g')
                sns.kdeplot((t1[feature]/365).dropna(), label = 'Défaillant', color='r')    
                plt.axvline(float(client_feature_val/365), color="blue", \
                            linestyle='--', label = 'Position Client')

            else:    
                sns.kdeplot(t0[feature].dropna(), label = 'Remboursé', color='g')
                sns.kdeplot(t1[feature].dropna(), label = 'Défaillant', color='r')
                plt.axvline(float(client_feature_val), color="blue", \
                            linestyle='--', label = 'Position Client')


            plt.title(title, fontsize='20', fontweight='bold')
            #plt.ylabel('Nombre de clients')
            #plt.xlabel(fontsize='14')
            plt.legend()
            plt.show()  
            st.pyplot(fig)
        else:
            st.write("Comparaison impossible car la valeur de cette variable n'est pas renseignée (NaN)")

    #@st.cache
    def univariate_categorical(applicationDF,feature,client_feature_val,\
                               titre,ylog=False,label_rotation=False,
                               horizontal_layout=True):
        if (client_feature_val.iloc[0] != np.nan):

            temp = applicationDF[feature].value_counts()
            df1 = pd.DataFrame({feature: temp.index,'Number of contracts': temp.values})

            categories = applicationDF[feature].unique()
            categories = list(categories)

            # Calculate the percentage of target=1 per category value
            cat_perc = applicationDF[[feature,\
                                      'TARGET']].groupby([feature],as_index=False).mean()
            cat_perc["TARGET"] = cat_perc["TARGET"]*100
            cat_perc.sort_values(by='TARGET', ascending=False, inplace=True)

            if(horizontal_layout):
                fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(12,5))
            else:
                fig, (ax1, ax2) = plt.subplots(nrows=2, figsize=(20,24))

            # 1. Subplot 1: Count plot of categorical column
            # sns.set_palette("Set2")
            s = sns.countplot(ax=ax1, 
                            x = feature, 
                            data=applicationDF,
                            hue ="TARGET",
                            order=cat_perc[feature],
                            palette=['g','r'])

            pos1 = cat_perc[feature].tolist().index(client_feature_val.iloc[0])
            #st.write(client_feature_val.iloc[0])

            # Define common styling
            ax1.set(ylabel = "Nombre de clients")
            ax1.set_title(titre, fontdict={'fontsize' : 15, 'fontweight' : 'bold'})   
            ax1.axvline(int(pos1), color="blue", linestyle='--', label = 'Position Client')
            ax1.legend(['Position Client','Remboursé','Défaillant' ])

            # If the plot is not readable, use the log scale.
            if ylog:
                ax1.set_yscale('log')
                ax1.set_ylabel("Count (log)",fontdict={'fontsize' : 15, \
                                                       'fontweight' : 'bold'})   
            if(label_rotation):
                s.set_xticklabels(s.get_xticklabels(),rotation=90)

            # 2. Subplot 2: Percentage of defaulters within the categorical column
            s = sns.barplot(ax=ax2, 
                            x = feature, 
                            y='TARGET', 
                            order=cat_perc[feature], 
                            data=cat_perc,
                            palette='Set2')

            pos2 = cat_perc[feature].tolist().index(client_feature_val.iloc[0])
            #st.write(pos2)

            if(label_rotation):
                s.set_xticklabels(s.get_xticklabels(),rotation=90)
            plt.ylabel('Pourcentage de défaillants [%]', fontsize=10)
            plt.tick_params(axis='both', which='major', labelsize=10)
            ax2.set_title(titre+" (% Défaillants)", \
                          fontdict={'fontsize' : 15, 'fontweight' : 'bold'})
            ax2.axvline(int(pos2), color="blue", linestyle='--', label = 'Position Client')
            ax2.legend()
            plt.show()
            st.pyplot(fig)
        else:
            st.write("Comparaison impossible car la valeur de cette variable n'est pas renseignée (NaN)")





    # Affichage de la table de données
    data_cleaned, test_X, test_X_transformed, description = load_data()
    
    df = test_X
    df_sample = df.sample(100)
    if st.sidebar.checkbox("Afficher les données brutes ", False):
        st.subheader("Jeu de données 'creditcard': Echantillon de 100 sur un portefeuille de " + df.shape[0] + " clients")
        st.write(df_sample)

    seed = 123

    ignore_columns = ['SK_ID_CURR', 'TARGET']
    features = [col for col in df.columns if col not in ignore_columns]


    #Chargement du modèle
    model = load_model()


    #######################################
    # SIDEBAR
    #######################################
    with st.sidebar:
        st.header("💰 Prêt à dépenser")

        st.write("## ID Client")
        id_list = df["SK_ID_CURR"].tolist()
        id_client = st.selectbox(
            "Sélectionner l'identifiant du client", id_list)

        st.write("## Actions à effectuer")
        show_credit_decision = st.checkbox("Afficher la décision de crédit")
        show_client_details = st.checkbox("Afficher les informations du client")
        show_client_comparison = st.checkbox("Comparer aux autres clients")
        shap_general = st.checkbox("Afficher la feature importance globale")
        if(st.checkbox("Aide description des features")):
            list_features = description.index.to_list()
            list_features = list(dict.fromkeys(list_features))
            feature = st.selectbox('Sélectionner une variable',\
                                   sorted(list_features))
            
            desc = description['Description'].loc[description.index == feature][:1]
            st.markdown('**{}**'.format(desc.iloc[0]))


    #######################################
    # HOME PAGE - MAIN CONTENT
    #######################################

    #Afficher l'ID Client sélectionné
    st.write("ID Client Sélectionné :", id_client)

    if (int(id_client) in id_list):

        client_info = get_client_info(df, id_client)

        model_choice = st.selectbox("Select Model",["LR","HistBoost","DecisionTree"])
        #-------------------------------------------------------
        # Afficher la décision de crédit
        #-------------------------------------------------------
        if (show_credit_decision):
            st.header('‍⚖️ Scoring et décision du modèle')

            API_url = str(id_client)
            client_data = test_X_transformed[test_X_transformed["SK_ID_CURR"] == id_client]
            features = [col for col in client_data.columns if col not in ["SK_ID_CURR"]]
            
            single_sample = np.array(client_data[features]).reshape(1,-1)

            #loaded_model = load_model("models/knn_hepB_model.pkl")
            prediction = model.predict(single_sample)
            pred_prob = model.predict_proba(single_sample).round(4)

            with st.spinner('Chargement du score du client...'):

                if prediction == 1:
                    st.warning("❌ Mauvais prospect")
                    pred_probability_score = {"Crédit Refusé ❌":pred_prob[0][0]*100,
                                                "Crédit Accordé ✅":pred_prob[0][1]*100}
                    st.subheader("Prediction Probability Score using {}".format(model_choice))
                    st.json(pred_probability_score)
                    st.subheader("Prescriptive Analytics")
                    #st.markdown(prescriptive_message_temp,unsafe_allow_html=True)

                else:
                    st.success(" Bon prospect ")
                    pred_probability_score = {"Crédit Refusé ❌":pred_prob[0][0]*100,
                                                "Crédit Accordé ✅":pred_prob[0][1]*100}
                    st.subheader("Prediction Probability Score using {}".format(model_choice))
                    st.json(pred_probability_score)
            
                #classe_predite = API_data['prediction']
                
                #if prediction == 1:
                #    decision = '❌ Mauvais prospect (Crédit Refusé)'
                #else:
                #    decision = '✅ Bon prospect (Crédit Accordé)'
                #proba = (1-pred_prob) * 100

                #client_score = np.around(proba, 2)

                #left_column, right_column = st.columns((1, 2))

                #left_column.markdown('Risque de défaut: **{}%**'.format(str(client_score)))
                #left_column.markdown('Seuil par défaut du modèle: **50%**')
                

        #-------------------------------------------------------
        # Afficher les informations du client
        #-------------------------------------------------------
        personal_info_cols = {
            'CODE_GENDER': "GENRE",
            'DAYS_BIRTH': "AGE",
            'NAME_FAMILY_STATUS': "STATUT FAMILIAL",
            'CNT_CHILDREN': "NB ENFANTS",
            'FLAG_OWN_CAR': "POSSESSION VEHICULE",
            'FLAG_OWN_REALTY': "POSSESSION BIEN IMMOBILIER",
            'NAME_EDUCATION_TYPE': "NIVEAU EDUCATION",
            'OCCUPATION_TYPE': "EMPLOI",
            'DAYS_EMPLOYED': "NB ANNEES EMPLOI",
            'AMT_INCOME_TOTAL': "REVENUS",
            'AMT_CREDIT': "MONTANT CREDIT", 
            'NAME_CONTRACT_TYPE': "TYPE DE CONTRAT",
            'AMT_ANNUITY': "MONTANT ANNUITES",
            'NAME_INCOME_TYPE': "TYPE REVENUS",
            #'EXT_SOURCE_1': "EXT_SOURCE_1",
            'EXT_SOURCE_2': "EXT_SOURCE_2",
            'EXT_SOURCE_3': "EXT_SOURCE_3",
        }
        default_list=["GENRE","AGE","STATUT FAMILIAL","NB ENFANTS","REVENUS","MONTANT CREDIT"]
        numerical_features = ['DAYS_BIRTH', 'CNT_CHILDREN', 'DAYS_EMPLOYED', 'AMT_INCOME_TOTAL','AMT_CREDIT','AMT_ANNUITY','EXT_SOURCE_2','EXT_SOURCE_3']
        rotate_label = ["NAME_FAMILY_STATUS", "NAME_EDUCATION_TYPE"]
        horizontal_layout = ["OCCUPATION_TYPE", "NAME_INCOME_TYPE"]
        
        if (show_client_details):
            st.header('‍🧑 Informations relatives au client')

            with st.spinner('Chargement des informations relatives au client...'):
                personal_info_df = client_info[list(personal_info_cols.keys())]
                #personal_info_df['SK_ID_CURR'] = client_info['SK_ID_CURR']
                personal_info_df.rename(columns=personal_info_cols, inplace=True)
                personal_info_df["AGE"] = int(round(personal_info_df["AGE"]/365*(-1)))
                personal_info_df["NB ANNEES EMPLOI"] = int(round(personal_info_df["NB ANNEES EMPLOI"]/365*(-1)))

                filtered = st.multiselect("Choisir les informations à afficher", \
                                          options=list(personal_info_df.columns),\
                                          default=list(default_list))

                df_info = personal_info_df[filtered] 
                df_info['SK_ID_CURR'] = client_info['SK_ID_CURR']
                df_info = df_info.set_index('SK_ID_CURR')

                show_table_format = st.checkbox("Afficher les informations sous forme de Table ")
                if (show_table_format):
                    st.table(df_info.astype(str).T)

                show_json_format = st.checkbox("Afficher les informations au format json")
                result = df_info.to_json(orient="records")
                parsed = json.loads(result)
                if (show_json_format):
                    st.json(parsed)


                show_all_info = st.checkbox("Afficher toutes les informations (dataframe brute)")
                if (show_all_info):
                    st.dataframe(client_info)


                
                

        #-------------------------------------------------------
        # Comparer le client sélectionné à d'autres clients
        #-------------------------------------------------------
        if (show_client_comparison):
            st.header('‍👀 Comparaison aux autres clients')
            #st.subheader("Comparaison avec l'ensemble des clients")
            with st.expander("🔍 Explication de la comparaison faite"):
                st.write("Lorsqu'une variable est sélectionnée, un graphique montrant la distribution de cette variable selon la classe (remboursé ou défaillant) sur l'ensemble des clients (dont on connait l'état de remboursement de crédit) est affiché avec une matérialisation du positionnement du client actuel.") 

            with st.spinner('Chargement de la comparaison liée à la variable sélectionnée'):
                var = st.selectbox("Sélectionner une variable",\
                                   list(personal_info_cols.values()))
                feature = list(personal_info_cols.keys())\
                [list(personal_info_cols.values()).index(var)]    

                if (feature in numerical_features):                
                    plot_distribution(data_cleaned, feature, client_info[feature], var)   
                elif (feature in rotate_label):
                    univariate_categorical(data_cleaned, feature, \
                                           client_info[feature], var, False, True)
                elif (feature in horizontal_layout):
                    univariate_categorical(data_cleaned, feature, \
                                           client_info[feature], var, False, True, True)
                else:
                    univariate_categorical(data_cleaned, feature, client_info[feature], var)


        #-------------------------------------------------------
        # Afficher la feature importance globale
        #-------------------------------------------------------
        if (shap_general):
            st.header('‍Feature importance globale')

            st.image('global_feature_importance.png')


            
    else:    
        st.markdown("**Identifiant non reconnu**")


if __name__ == '__main__':
    main() 