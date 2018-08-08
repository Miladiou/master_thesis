#include <iostream>
#include <random>
#include "./MultiVariatePointProcess/include/PlainHawkes.h"
#include "./MultiVariatePointProcess/include/OgataThinning.h"


int main()
{


    // Set the random number generator seed to the current machine time
    srand((unsigned int) time(0));

    // Used to generate randomness for the bernoulli distribution
    unsigned time_ui = int(time(NULL));
    std::default_random_engine generator (time_ui);


    unsigned nodes_nbr = 10, params_nbr = nodes_nbr * (nodes_nbr + 1); // Number of users in the network
    unsigned fake_nbr = 2, real_nbr = 2;  // Number of nodes that emit fake/real pieces of news
    double mu = 1, sparsity = 0.02; // Network parameters

    Eigen::MatrixXd Beta_ = Eigen::MatrixXd::Ones(nodes_nbr, nodes_nbr);

    // Set the exogenous intensities between 0 and 0.5 for both the fake and real news processes
    Eigen::VectorXd fake_params(params_nbr);
    Eigen::VectorXd real_params(params_nbr);
    Eigen::VectorXd fake_exo_int = (Eigen::VectorXd::Random(fake_nbr) + Eigen::VectorXd::Ones(fake_nbr))/4.0;
    //Eigen::VectorXd real_exo_int = (Eigen::VectorXd::Random(real_nbr) + Eigen::VectorXd::Ones(real_nbr))/4.0;
    Eigen::VectorXd real_exo_int = Eigen::VectorXd::Zero(fake_nbr);
    Eigen::VectorXd no_exo_int_fake = Eigen::VectorXd::Zero(nodes_nbr - fake_nbr);
    Eigen::VectorXd no_exo_int_real = Eigen::VectorXd::Zero(nodes_nbr - real_nbr);

    // Set the endogenous intensities between 0 and 0.5 for both processes
    // Assumptions: influence relations are not reciprocal, there might be no self-influence, campaigner nodes from one campaign do not impact the other campaign, relations between users are the same in both campaigns albeit with different weights
    Eigen::VectorXd fake_endo_int = (Eigen::VectorXd::Random(nodes_nbr * nodes_nbr) + Eigen::VectorXd::Ones(nodes_nbr * nodes_nbr))/4.0;
    Eigen::VectorXd real_endo_int = (Eigen::VectorXd::Random(nodes_nbr * nodes_nbr) + Eigen::VectorXd::Ones(nodes_nbr * nodes_nbr))/4.0;
    Eigen::VectorXd fake_inhibition(nodes_nbr);
    Eigen::VectorXd real_inhibition(nodes_nbr);
    fake_inhibition << Eigen::VectorXd::Ones(fake_nbr), Eigen::VectorXd::Zero(real_nbr), Eigen::VectorXd::Ones(nodes_nbr - fake_nbr - real_nbr);
    real_inhibition << Eigen::VectorXd::Zero(fake_nbr), Eigen::VectorXd::Ones(nodes_nbr - fake_nbr);

    // Remove the influence of fake campaigner nodes in the real news campaign and vice-versa for the fake news campaign
    for (int i = 0; i < nodes_nbr; ++i) {

        Eigen::VectorXd current_fake_row = fake_endo_int.segment(nodes_nbr * i, nodes_nbr);
        Eigen::VectorXd current_real_row = real_endo_int.segment(nodes_nbr * i, nodes_nbr);

        if (i >= fake_nbr && i < fake_nbr + real_nbr) current_fake_row << Eigen::VectorXd::Zero(nodes_nbr);
        else current_fake_row = current_fake_row.cwiseProduct(fake_inhibition);

        if (i < fake_nbr) current_real_row << Eigen::VectorXd::Zero(nodes_nbr);
        else current_real_row = current_real_row.cwiseProduct(real_inhibition);

        fake_endo_int.segment(nodes_nbr * i, nodes_nbr) << current_fake_row;
        real_endo_int.segment(nodes_nbr * i, nodes_nbr) << current_real_row;

    }


    // Remove edges to obtain a sparse network
    std::bernoulli_distribution distribution(sparsity);
    Eigen::VectorXd binary_vector(nodes_nbr * nodes_nbr);
    for (int i = 0; i < nodes_nbr * nodes_nbr; ++ i) {binary_vector(i) = distribution(generator);}
    fake_endo_int = fake_endo_int.cwiseProduct(binary_vector);
    real_endo_int = real_endo_int.cwiseProduct(binary_vector);

    fake_params << fake_exo_int, no_exo_int_fake, fake_endo_int;
    real_params << real_exo_int, no_exo_int_real, real_endo_int;

    // Create adjacency matrix. OBS: Columns are dominant with Eigen (killen fran linen paverkar killen fran kolumnen)
    Eigen::Map<Eigen::MatrixXd> adjacency(binary_vector.data(), nodes_nbr, nodes_nbr);
    adjacency.diagonal() = Eigen::VectorXd::Ones(nodes_nbr);


    // Create one Hawkes model for the diffusion of fake news and one for the diffusion of real news
    PlainHawkes fake_hawkes(params_nbr, nodes_nbr, Beta_);
    PlainHawkes real_hawkes(params_nbr, nodes_nbr, Beta_);
	fake_hawkes.SetParameters(fake_params);
    real_hawkes.SetParameters(real_params);


    // Simulations
    double time_fonstret = 10.0;
    unsigned events_nbr = 100;

    std::vector<double> vec_T(1, time_fonstret);
    std::vector<Sequence> fake_sequences;
    std::vector<Sequence> real_sequences;
    Eigen::VectorXd fake_counts = Eigen::VectorXd::Zero(nodes_nbr);
    Eigen::VectorXd real_counts = Eigen::VectorXd::Zero(nodes_nbr);

    OgataThinning ogata(nodes_nbr);
    ogata.Simulate(fake_hawkes, vec_T, fake_sequences);
    ogata.Simulate(real_hawkes, vec_T, real_sequences);
    //ogata.Simulate(hawkes, events_nbr, 1, sequences);

    Sequence current_fake = fake_sequences[0];
    Sequence current_real = real_sequences[0];
    current_fake.Counting(fake_counts);
    current_real.Counting(real_counts);
    double T_ = current_fake.GetTimeWindow();

    // Count the exposure of users to fake/real news (should be transpose of adjacency)
    Eigen::VectorXd fake_exposure = adjacency * fake_counts;
    Eigen::VectorXd real_exposure = adjacency * real_counts;

    //current_fake.PrintSequence();

    /*
    for (int i = 0; i < nodes_nbr; ++i) {
        std::cout << fake_counts[i] << std::endl;
    }
    */

    std::cout << fake_counts << std::endl;
    std::cout << adjacency << std::endl;


}
