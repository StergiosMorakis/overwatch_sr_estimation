from model import OwModel
import warnings

if __name__ == '__main__':
	warnings.filterwarnings("ignore")
	model = OwModel().load_model()
	while input('Make prediction (Y/n)? '.ljust(28)).lower() in (
		'yes'[:i] for i in range(1, 4)
	):
		'''
			Model
			independent variables:
				1) # wins
				2) # losses
			dependent variables:
				1) skill_rating
		'''
		wins = input('Insert player wins: '.ljust(28))
		losses = input('Insert player losses: '.ljust(28))
		try:
			wins = int(wins)
			losses = int(losses)
		except:
			print('Invalid values.')
			continue
		print('Estimated skill rating:'.ljust(27), model.predict(wins, losses), '\n{}\n'.format('*'*8))
