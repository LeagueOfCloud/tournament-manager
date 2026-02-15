using System.Data;
using MySqlConnector;

namespace pickems_evaluator.Data;

public static class DatabaseHelper
{

    private static MySqlConnectionStringBuilder Connection;

    public static async Task<List<T>> ExecuteQueryAsync<T>(string query, Func<IDataReader, T> mapper)
    {
        if (Connection is null)
        {
            SetDatabaseConnection();
        }

        var results = new List<T>();

        try
        {
            await using var connection = new MySqlConnection(Connection.ConnectionString);
            await connection.OpenAsync();
            await using var command = connection.CreateCommand();
            command.CommandText = query;
            await using var reader = await command.ExecuteReaderAsync();
            while (reader.Read())
            {
                results.Add(mapper(reader));
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Database error: {ex.Message}");
            throw;
        }

        return results;
    }

    public static async Task ExecuteUpdateAsync(string query)
    {
        if (Connection is null)
        {
            SetDatabaseConnection();
        }

        try
        {
            await using var connection = new MySqlConnection(Connection.ConnectionString);
            await connection.OpenAsync();
            await using var command = connection.CreateCommand();
            command.CommandText = query;
            await command.ExecuteNonQueryAsync();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Database error: {ex.Message}");
            throw;
        }
    }

    private static void SetDatabaseConnection()
    {
        var username = Environment.GetEnvironmentVariable("DB_USER")
            ?? throw new InvalidOperationException("DB_USERNAME not set");
        var password = Environment.GetEnvironmentVariable("DB_PASSWORD")
            ?? throw new InvalidOperationException("DB_PASSWORD not set");
        var host = Environment.GetEnvironmentVariable("DB_HOST")
            ?? throw new InvalidOperationException("DB_HOST not set");
        var port = Environment.GetEnvironmentVariable("DB_PORT")
            ?? throw new InvalidOperationException("DB_PORT not set");
        var name = Environment.GetEnvironmentVariable("DB_NAME")
            ?? throw new InvalidOperationException("DB_NAME not set");

        Connection = new MySqlConnectionStringBuilder
        {
            Server = host,
            UserID = username,
            Password = password,
            Database = name,
        };
    }
}