import streamlit_authenticator as stauth

senhas = ['minha_senha123', 'senhaCoord456']

hashes = stauth.Hasher(senhas).generate()
print(hashes)
