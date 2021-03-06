import tensorflow as tf
import numpy as np


class PolicyGradient:
    def __init__(self, hidden_net, n_in=4, n_out=2, lr=0.01, sess=tf.Session()):
        self.n_in = n_in
        self.hidden_net = hidden_net
        self.n_out = n_out
        self.lr = lr
        self.sess = sess
        self.build_graph()
    # end constructor


    def build_graph(self):
        self.add_forward_path()
        self.add_backward_path()
    # end method build_graph


    def add_forward_path(self):
        self.X = tf.placeholder(tf.float32, shape=[None, self.n_in])
        hidden = self.hidden_net(self.X)
        self.logits = tf.layers.dense(hidden, self.n_out)
        outputs = tf.nn.softmax(self.logits)

        self.action = tf.multinomial(tf.log(outputs), num_samples=1)
        self.action_one_hot = tf.one_hot(tf.squeeze(self.action), self.n_out)
    # end method build_forward_path


    def add_backward_path(self):
        loss = tf.nn.softmax_cross_entropy_with_logits(labels=self.action_one_hot, logits=self.logits)
        optimizer = tf.train.AdamOptimizer(self.lr)

        grads_and_vars = optimizer.compute_gradients(loss)
        self.gradients = [grad for grad, variable in grads_and_vars]

        self.gradient_placeholders = []
        grads_and_vars_feed = []
        for grad, variable in grads_and_vars:
            gradient_placeholder = tf.placeholder(tf.float32, shape=grad.get_shape())
            self.gradient_placeholders.append(gradient_placeholder)
            grads_and_vars_feed.append((gradient_placeholder, variable))
        
        self.train_op = optimizer.apply_gradients(grads_and_vars_feed)
    # end method add_backward_path


    def learn(self, env, n_games_per_update=10, n_max_steps=1000, n_iterations=250, discount_rate=0.95):
        self.sess.run(tf.global_variables_initializer())
        for iteration in range(n_iterations):
            print("Iteration: {}".format(iteration))

            all_rewards = []
            all_gradients = []
            for game in range(n_games_per_update):
                current_rewards = []
                current_gradients = []
                obs = env.reset()
                for step in range(n_max_steps):
                    action_val, gradients_val = self.sess.run([self.action, self.gradients], {self.X: np.atleast_2d(obs)})
                    obs, reward, done, info = env.step(action_val[0][0])
                    current_rewards.append(reward)
                    current_gradients.append(gradients_val)
                    if done:
                        break
                all_rewards.append(current_rewards)
                all_gradients.append(current_gradients)

            all_rewards = self.discount_and_normalize_rewards(all_rewards, discount_rate=discount_rate)
            feed_dict = {}
            for var_index, gradient_placeholder in enumerate(self.gradient_placeholders):
                mean_gradients = np.mean([reward * all_gradients[game_index][step][var_index]
                                          for game_index, rewards in enumerate(all_rewards)
                                          for step, reward in enumerate(rewards)], axis=0)
                feed_dict[gradient_placeholder] = mean_gradients
            self.sess.run(self.train_op, feed_dict)
    # end method learn

    def play(self, env):
        obs = env.reset()
        done = False
        count = 0
        while not done:
            env.render()
            action_val = self.sess.run(self.action, {self.X: np.atleast_2d(obs)})
            obs, reward, done, info = env.step(action_val[0][0])
            count += 1
        print(count)
    # end method play


    def discount_rewards(self, rewards, discount_rate):
        discounted_rewards = np.zeros(len(rewards))
        cumulative_rewards = 0
        for step in reversed(range(len(rewards))):
            cumulative_rewards = rewards[step] + cumulative_rewards * discount_rate
            discounted_rewards[step] = cumulative_rewards
        return discounted_rewards
    # end method discount_rewards


    def discount_and_normalize_rewards(self, all_rewards, discount_rate):
        all_discounted_rewards = [self.discount_rewards(rewards, discount_rate) for rewards in all_rewards]
        flat_rewards = np.concatenate(all_discounted_rewards)
        reward_mean = flat_rewards.mean()
        reward_std = flat_rewards.std()
        return [(discounted_rewards - reward_mean) / reward_std for discounted_rewards in all_discounted_rewards]
    # end method discount_and_normalize_rewards
